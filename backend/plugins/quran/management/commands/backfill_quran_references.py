"""
Django Management Command: backfill_quran_references
Enterprise-grade, server-side Quran verse reference extractor and intermediate table populator.

Reads historical posts directly from the database, identifies Quran Ayahs cited in the text
(both structured posts with Surah names and unstructured/narrative posts without Surah names),
and populates the `tafakor_post_plugin_references` table (PostPluginReference model).

Usage:
    python manage.py backfill_quran_references --dry-run
    python manage.py backfill_quran_references --topics=8,9
    python manage.py backfill_quran_references --topics=24,27 --clear-existing
"""

import os
import re
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple, Set, Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from apps.notes.models import Post, Topic
from apps.plugin_system.models import Plugin, PostPluginReference


# ==============================================================================
# 1. CANONICAL QURAN METADATA & PERSIAN SURAH NAMES (1..114)
# ==============================================================================

SURAH_NAMES_FA = {
    1: 'فاتحه', 2: 'بقره', 3: 'آل عمران', 4: 'نساء', 5: 'مائده', 6: 'انعام', 7: 'اعراف', 8: 'انفال',
    9: 'توبه', 10: 'یونس', 11: 'هود', 12: 'یوسف', 13: 'رعد', 14: 'ابراهیم', 15: 'حجر', 16: 'نحل',
    17: 'اسراء', 18: 'کهف', 19: 'مریم', 20: 'طه', 21: 'انبیاء', 22: 'حج', 23: 'مؤمنون', 24: 'نور',
    25: 'فرقان', 26: 'شعراء', 27: 'نمل', 28: 'قصص', 29: 'عنکبوت', 30: 'روم', 31: 'لقمان', 32: 'سجده',
    33: 'احزاب', 34: 'سبأ', 35: 'فاطر', 36: 'یس', 37: 'صافات', 38: 'ص', 39: 'زمر', 40: 'غافر',
    41: 'فصلت', 42: 'شوری', 43: 'زخرف', 44: 'دخان', 45: 'جاثیه', 46: 'احقاف', 47: 'محمد', 48: 'فتح',
    49: 'حجرات', 50: 'ق', 51: 'ذاریات', 52: 'طور', 53: 'نجم', 54: 'قمر', 55: 'الرحمن', 56: 'واقعه',
    57: 'حدید', 58: 'مجادله', 59: 'حشر', 60: 'ممتحنه', 61: 'صف', 62: 'جمعه', 63: 'منافقون', 64: 'تغابن',
    65: 'طلاق', 66: 'تحریم', 67: 'ملک', 68: 'قلم', 69: 'حاقه', 70: 'معارج', 71: 'نوح', 72: 'جن',
    73: 'مزمل', 74: 'مدثر', 75: 'قیامت', 76: 'انسان', 77: 'مرسلات', 78: 'نبأ', 79: 'نازعات', 80: 'عبس',
    81: 'تکویر', 82: 'انفطار', 83: 'مطففین', 84: 'انشقاق', 85: 'بروج', 86: 'طارق', 87: 'اعلی', 88: 'غاشیه',
    89: 'فجر', 90: 'بلد', 91: 'شمس', 92: 'لیل', 93: 'ضحی', 94: 'شرح', 95: 'تین', 96: 'علق',
    97: 'قدر', 98: 'بینه', 99: 'زلزله', 100: 'عادیات', 101: 'قارعه', 102: 'تکاثر', 103: 'عصر', 104: 'همزه',
    105: 'فیل', 106: 'قریش', 107: 'ماعون', 108: 'کوثر', 109: 'کافرون', 110: 'نصر', 111: 'مسد', 112: 'اخلاص',
    113: 'فلق', 114: 'ناس'
}

HISTORICAL_SURAH_ALIASES = {
    'توحید': 112,
    'دهر': 76,
    'هل اتی': 76,
    'بنی اسراییل': 17,
    'بنی اسرائیل': 17,
    'اسرا': 17,
    'مومن': 40,
    'انشراح': 94,
    'برائت': 9,
    'برائه': 9,
}


# ==============================================================================
# 2. HIGH-PRECISION TEXT NORMALIZATION (Arabic & Persian)
# ==============================================================================

def normalize_text(text: str) -> str:
    """
    Standardizes Quranic Arabic & Persian orthography for deterministic matching:
    1. Converts dagger alef (U+0670) to standard alef (ا) before stripping marks.
    2. Strips all Tashkeel, Sukun, Tanwin, and Quranic stop symbols.
    3. Standardizes Yeh (ي, ى -> ی), Kaf (ك -> ک), Teh Marbuta (ة -> ه).
    4. Unifies Alef variations (أ, إ, آ, ٱ, ء -> ا).
    5. Collapses repeated alefs (e.g. ء + ا -> ا).
    6. Converts Arabic & Persian numerals to ASCII digits.
    7. Standardizes vocative particles ('یا ایها', 'یا اهل', etc.).
    """
    if not text:
        return ""

    # Dagger alef to standard alef
    text = text.replace('\u0670', 'ا')

    # Remove Tashkeel & Quranic annotations
    text = re.sub(r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED]', '', text)

    # Standardize letters
    text = text.replace('ي', 'ی').replace('ى', 'ی').replace('ك', 'ک')
    text = re.sub(r'[أإآٱء]', 'ا', text)
    text = text.replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ی')
    text = re.sub(r'ا+', 'ا', text)

    # Convert Persian/Arabic digits to ASCII
    for i, (ar, fa) in enumerate(zip('٠١٢٣٤٥٦٧٨٩', '۰۱۲۳۴۵۶۷۸۹')):
        text = text.replace(ar, str(i)).replace(fa, str(i))

    # Clean punctuation
    text = re.sub(r'[^\w\s]', ' ', text)

    # Vocative particle separator
    text = re.sub(r'\bیا(?=ایها|اهل|بنی|مریم|داود|ابراهیم|موسی|عیسی|قوم)', 'یا ', text)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


# ==============================================================================
# 3. COMMAND IMPLEMENTATION
# ==============================================================================

class Command(BaseCommand):
    help = "Extract Quran Ayah references from historical posts and populate PostPluginReference table."

    def add_arguments(self, parser):
        parser.add_argument(
            '--topics',
            type=str,
            default=None,
            help='Comma-separated topic IDs to process (e.g. 8,9 or 24,27). Defaults to all active topics.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Analyze and report matches without writing to the database.'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Delete existing Quran PostPluginReference rows for the processed posts before backfilling.'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Batch size for bulk_create operations (default: 500).'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surah_name_to_num: Dict[str, int] = {}
        self.surah_max_ayahs: Dict[int, int] = {}
        self.ayah_by_num: Dict[int, List[Tuple[int, str, Set[str], int]]] = {}
        self.all_ayahs: List[Tuple[int, int, str, Set[str]]] = []
        self._init_quran_catalog()

    def _init_quran_catalog(self):
        """Builds in-memory Quran indexes from bundled quran-simple.json in <0.2s."""
        # 1. Surah names mapping
        for num, fa_name in SURAH_NAMES_FA.items():
            norm = normalize_text(fa_name)
            self.surah_name_to_num[norm] = num
            self.surah_name_to_num['ال' + norm] = num
            if norm.startswith('ال') and len(norm) > 2:
                self.surah_name_to_num[norm[2:]] = num

        for alias, num in HISTORICAL_SURAH_ALIASES.items():
            self.surah_name_to_num[normalize_text(alias)] = num

        # 2. Load Hafs 6,236 Ayahs catalog
        plugin_dir = Path(__file__).resolve().parent.parent.parent
        quran_json_path = plugin_dir / 'data' / 'full' / 'quran-simple.json'

        if not quran_json_path.exists():
            raise CommandError(f"Quran dataset not found at: {quran_json_path}")

        with open(quran_json_path, 'r', encoding='utf-8') as f:
            quran_data = json.load(f)['data']

        for surah in quran_data['surahs']:
            s_num = surah['number']
            ayahs = surah['ayahs']
            self.surah_max_ayahs[s_num] = len(ayahs)

            # Arabic name indexing
            norm_ar = normalize_text(surah['name']).replace('سوره', '').strip()
            self.surah_name_to_num[norm_ar] = s_num
            if norm_ar.startswith('ال') and len(norm_ar) > 2:
                self.surah_name_to_num[norm_ar[2:]] = s_num

            for ayah in ayahs:
                a_num = ayah['numberInSurah']
                norm_a = normalize_text(ayah['text'])
                words = set(w for w in norm_a.split() if len(w) > 2)
                total_w = len(norm_a.split())

                self.ayah_by_num.setdefault(a_num, []).append((s_num, norm_a, words, total_w))
                self.all_ayahs.append((s_num, a_num, norm_a, words))

    def resolve_surah_name(self, text: str) -> int:
        clean = normalize_text(text)
        clean = re.sub(r'^(سوره|سورة|مبارکه|مباركه)\s+', '', clean)
        clean = re.sub(r'\s+(سوره|سورة|مبارکه|مباركه)$', '', clean).strip()
        return self.surah_name_to_num.get(clean)

    def extract_quran_references(self, content: str) -> List[Tuple[int, int]]:
        """
        Multi-tier extractor identifying Quran Ayahs from post text:
        - Tier 1: Explicit pattern ('سوره X آیه Y' or '[سوره X: Y]')
        - Tier 2: Structured format (Line 1: Surah name, parentheses with Ayah numbers)
        - Tier 3: Hafs Matcher with parenthesized Ayah numbers and word-set verification
        - Tier 4: Hafs Fulltext prefix/word-set scan for unannotated Arabic verses
        """
        if not content or not content.strip():
            return []

        found: Set[Tuple[int, int]] = set()

        def add_ref(s_num: int, a_num: int):
            if 1 <= s_num <= 114:
                max_a = self.surah_max_ayahs.get(s_num, 286)
                if 1 <= a_num <= max_a:
                    found.add((s_num, a_num))

        # --- Tier 1: Explicit pattern ---
        for m in re.finditer(r'سوره\s+(?:مبارکه\s+)?([^\s،:؛\(\)\[\]]+)\s*(?:،|:)?\s*آیه\s*([0-9۰-۹٠-٩]+)', content):
            s_num = self.resolve_surah_name(m.group(1))
            try:
                a_num = int(normalize_text(m.group(2)))
                if s_num:
                    add_ref(s_num, a_num)
            except ValueError:
                pass

        for m in re.finditer(r'\[\s*(?:سوره\s+)?([^\s،:؛\(\)\[\]]+)\s*[:،]\s*([0-9۰-۹٠-٩]+)\s*\]', content):
            s_num = self.resolve_surah_name(m.group(1))
            try:
                a_num = int(normalize_text(m.group(2)))
                if s_num:
                    add_ref(s_num, a_num)
            except ValueError:
                pass

        # --- Tier 2: Structured header format ---
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        current_surah = None
        for line in lines:
            if len(line) <= 25 and not any(c in line for c in '.:؛!؟…'):
                cand = self.resolve_surah_name(line)
                if cand:
                    current_surah = cand
                    continue
            if current_surah:
                for vm in re.finditer(r'[\(（]([0-9۰-۹٠-٩]{1,3})[\)）]', line):
                    try:
                        a_num = int(normalize_text(vm.group(1)))
                        add_ref(current_surah, a_num)
                    except ValueError:
                        pass

        # --- Tier 3: Hafs Matcher (Parenthesized numbers + word overlap) ---
        norm = normalize_text(content)
        pwords = set(w for w in norm.split() if len(w) > 2)
        parens = [int(m) for m in re.findall(r'[\(（]([0-9۰-۹٠-٩]{1,3})[\)）]', content)]

        for pnum in parens:
            candidates = self.ayah_by_num.get(pnum, [])
            for s_num, norm_ayah, awords, total_w in candidates:
                overlap = len(pwords.intersection(awords))
                if (total_w <= 4 and overlap >= 2) or (total_w > 4 and overlap >= 3):
                    add_ref(s_num, pnum)

        # --- Tier 4: Hafs Fulltext scan for posts without Surah name and without numbers ---
        if not found and len(pwords) >= 4:
            first_line = content.split('\n')[0]
            first_part_words = set(w for w in normalize_text(first_line).split() if len(w) > 2)
            if len(first_part_words) >= 3:
                for s_num, a_num, norm_ayah, awords in self.all_ayahs:
                    overlap = len(first_part_words.intersection(awords))
                    if (len(awords) <= 4 and overlap >= 2) or (len(awords) > 4 and overlap >= 4):
                        add_ref(s_num, a_num)
                        break

        # Return sorted list of tuples (surah_number, ayah_number)
        return sorted(list(found), key=lambda x: (x[0], x[1]))

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']
        batch_size = options['batch_size']
        topics_arg = options['topics']

        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("  TAFAKOR QURAN REFERENCE BACKFILL ENGINE"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(f"Mode: {'DRY-RUN (Simulate only)' if dry_run else 'PRODUCTION COMMIT'}")
        self.stdout.write(f"Batch size: {batch_size}")
        self.stdout.write(f"Clear existing: {clear_existing}")

        # 1. Resolve Target Topics
        topic_qs = Topic.objects.all()
        if topics_arg:
            try:
                topic_ids = [int(tid.strip()) for tid in topics_arg.split(',') if tid.strip()]
                topic_qs = topic_qs.filter(id__in=topic_ids)
            except ValueError:
                raise CommandError("Invalid --topics argument. Must be comma-separated integers.")

        topics = list(topic_qs.order_by('id'))
        if not topics:
            self.stdout.write(self.style.WARNING("No matching topics found."))
            return

        self.stdout.write(f"Target Topics ({len(topics)}): {', '.join(f'#{t.id} ({t.title})' for t in topics)}")

        # 2. Ensure Quran Plugin exists in DB
        plugin = None
        if not dry_run:
            plugin, created = Plugin.objects.get_or_create(
                identifier='quran',
                defaults={
                    'name': 'قرآن کریم',
                    'description': 'افزونه رسمی اتصال یادداشت‌ها به آیات قرآن کریم',
                    'version': '1.0.0',
                    'is_active': True,
                    'is_system': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS("Created Quran Plugin entry in database."))

        start_time = time.time()
        total_posts_scanned = 0
        total_posts_matched = 0
        total_references_created = 0

        # 3. Process Topic by Topic
        for topic in topics:
            self.stdout.write("\n" + "-" * 70)
            self.stdout.write(f"Processing Topic #{topic.id}: {topic.title}")

            posts = Post.objects.filter(topic=topic).order_by('id')
            post_count = posts.count()
            total_posts_scanned += post_count

            if post_count == 0:
                self.stdout.write("  No posts in this topic.")
                continue

            if clear_existing and not dry_run and plugin:
                deleted_count, _ = PostPluginReference.objects.filter(
                    post__in=posts,
                    plugin=plugin,
                    resource_type='ayah'
                ).delete()
                self.stdout.write(f"  Cleared {deleted_count} existing Quran references.")

            topic_matched_posts = 0
            topic_references = []

            for post in posts.iterator(chunk_size=batch_size):
                refs = self.extract_quran_references(post.content or '')
                if refs:
                    topic_matched_posts += 1
                    for s_num, a_num in refs:
                        surah_name = SURAH_NAMES_FA.get(s_num, f'سوره {s_num}')
                        ref_obj = PostPluginReference(
                            post=post,
                            plugin=plugin,
                            resource_type='ayah',
                            external_id=f"surah:{s_num},ayah:{a_num}",
                            metadata={
                                'surah_number': s_num,
                                'ayah_number': a_num,
                                'surah_name': surah_name
                            }
                        )
                        topic_references.append(ref_obj)

            # Insert references into DB in batches
            if not dry_run and topic_references:
                with transaction.atomic():
                    PostPluginReference.objects.bulk_create(
                        topic_references,
                        batch_size=batch_size,
                        ignore_conflicts=True
                    )

            total_posts_matched += topic_matched_posts
            total_references_created += len(topic_references)

            pct = (topic_matched_posts / post_count * 100) if post_count > 0 else 0
            self.stdout.write(
                f"  Results for #{topic.id}: {topic_matched_posts}/{post_count} posts matched ({pct:.1f}%), "
                f"{len(topic_references)} Ayah references generated."
            )

        elapsed = time.time() - start_time

        # 4. Final Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("  BACKFILL EXECUTION SUMMARY"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"Total Posts Scanned:        {total_posts_scanned}")
        self.stdout.write(f"Total Posts Matched:        {total_posts_matched} ({(total_posts_matched/total_posts_scanned*100):.1f}%)" if total_posts_scanned > 0 else "0")
        self.stdout.write(f"Total Ayah References:      {total_references_created}")
        self.stdout.write(f"Time Elapsed:               {elapsed:.2f} seconds")
        self.stdout.write(f"Database Operations:        {'SIMULATED (Dry Run)' if dry_run else 'COMMITTED SUCCESSFULLY'}")
        self.stdout.write("=" * 70)

