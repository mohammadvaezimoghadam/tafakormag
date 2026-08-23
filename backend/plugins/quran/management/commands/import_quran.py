"""
Source-driven atomic JSON Quran importer management command.
Supports dynamic input formats, seed fixtures, sample CI datasets, and transactional rollback.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah
from plugins.quran.services.normalizer import normalize_quran_text

BISMILLAH_PREFIX_REGEX = re.compile(
    r'^(?:بِسْمِ\s*[\u0671\u0627]للَّهِ\s*[\u0671\u0627]لرَّحْمَ[ٰـ\u0670]?نِ\s*[\u0671\u0627]لرَّحِيمِ|'
    r'بسم\s*الله\s*الرحمن\s*الرحیم|'
    r'بسم\s*الله\s*الرحمن\s*الرحيم)\s*',
    re.UNICODE | re.IGNORECASE
)


class Command(BaseCommand):
    help = "Source-driven atomic Quran dataset importer."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to JSON edition file')
        parser.add_argument('--dir', type=str, help='Path to directory containing JSON edition files')
        parser.add_argument('--seed', action='store_true', help='Import bundled surahs, juzs, and default seed editions')
        parser.add_argument('--sample', action='store_true', help='Import sample test dataset (Surahs 1, 112-114) for fast tests')
        parser.add_argument('--dry-run', action='store_true', help='Validate without writing to database')
        parser.add_argument('--force', action='store_true', help='Overwrite existing editions and ayahs')
        parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for bulk_create (default: 1000)')

    def get_data_dir(self) -> Path:
        plugin_dir = Path(__file__).resolve().parent.parent.parent
        return plugin_dir / 'data'

    def handle(self, *args, **options):
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        batch_size = options.get('batch_size', 1000)
        data_dir = self.get_data_dir()

        # Step 1: Ensure canonical Surahs (114) and Juzs (30) metadata are present
        self.ensure_surahs_and_juzs(data_dir, force=force, dry_run=dry_run)

        # Step 2: Handle specific invocation mode
        if options.get('sample'):
            self.import_sample_data(data_dir, force=force, dry_run=dry_run, batch_size=batch_size)
        elif options.get('seed'):
            self.import_seed_data(data_dir, force=force, dry_run=dry_run, batch_size=batch_size)
        elif options.get('file'):
            self.import_from_file(Path(options['file']), force=force, dry_run=dry_run, batch_size=batch_size)
        elif options.get('dir'):
            self.import_from_directory(Path(options['dir']), force=force, dry_run=dry_run, batch_size=batch_size)
        else:
            # Default to seed data if no options specified
            self.stdout.write(self.style.NOTICE("No flag specified. Defaulting to --sample import..."))
            self.import_sample_data(data_dir, force=force, dry_run=dry_run, batch_size=batch_size)

    def ensure_surahs_and_juzs(self, data_dir: Path, force: bool = False, dry_run: bool = False):
        """Ensures 114 Surahs and 30 Juzs are populated in the database."""
        surahs_file = data_dir / 'surahs.json'
        juzs_file = data_dir / 'juzs.json'

        surah_count = QuranSurah.objects.count() if not dry_run else 0
        if surah_count < 114 or force:
            if not surahs_file.exists():
                raise CommandError(f"Missing required surahs metadata file: {surahs_file}")

            with open(surahs_file, 'r', encoding='utf-8') as f:
                surahs_data = json.load(f)

            surahs_list = surahs_data if isinstance(surahs_data, list) else surahs_data.get('surahs', [])
            if not dry_run:
                with transaction.atomic():
                    for s in surahs_list:
                        QuranSurah.objects.update_or_create(
                            number=s['number'],
                            defaults={
                                'name': s['name'],
                                'english_name': s.get('english_name') or s.get('englishName', ''),
                                'english_name_translation': s.get('english_name_translation') or s.get('englishNameTranslation', ''),
                                'revelation_type': s.get('revelation_type') or s.get('revelationType', 'Meccan'),
                                'ayah_count': s.get('ayah_count') or s.get('numberOfAyahs', 0),
                                'order_of_revelation': s.get('order_of_revelation') or s.get('orderOfRevelation'),
                                'page_start': s.get('page_start') or s.get('pageStart'),
                                'page_end': s.get('page_end') or s.get('pageEnd'),
                                'juz_start': s.get('juz_start') or s.get('juzStart', 1),
                                'bismillah_pre': s.get('bismillah_pre', s['number'] != 9),
                            }
                        )
            self.stdout.write(self.style.SUCCESS(f"Loaded {len(surahs_list)} Quran Surahs metadata."))

        juz_count = QuranJuz.objects.count() if not dry_run else 0
        if juz_count < 30 or force:
            if not juzs_file.exists():
                raise CommandError(f"Missing required juzs metadata file: {juzs_file}")

            with open(juzs_file, 'r', encoding='utf-8') as f:
                juzs_data = json.load(f)

            juzs_list = juzs_data if isinstance(juzs_data, list) else juzs_data.get('juzs', [])
            if not dry_run:
                surahs_map = {s.number: s for s in QuranSurah.objects.all()}
                with transaction.atomic():
                    for j in juzs_list:
                        start_s = surahs_map.get(j['start_surah'])
                        end_s = surahs_map.get(j['end_surah'])
                        if start_s and end_s:
                            QuranJuz.objects.update_or_create(
                                number=j['number'],
                                defaults={
                                    'name': j.get('name', f"جزء {j['number']}"),
                                    'start_surah': start_s,
                                    'start_ayah': j['start_ayah'],
                                    'end_surah': end_s,
                                    'end_ayah': j['end_ayah'],
                                    'surah_mapping': j.get('surah_mapping', []),
                                }
                            )
            self.stdout.write(self.style.SUCCESS(f"Loaded {len(juzs_list)} Quran Juzs metadata."))

    def extract_editions_and_ayahs(self, raw_data, fallback_identifier: str = "custom") -> List[Tuple[dict, list]]:
        """
        Dynamically inspects the input JSON structure and normalizes it to:
        [(edition_dict, list_of_raw_ayah_dicts), ...]
        """
        results = []

        if isinstance(raw_data, list):
            # Check if list of edition items or list of ayahs
            if len(raw_data) > 0 and 'surahs' in raw_data[0]:
                for item in raw_data:
                    results.extend(self.extract_editions_and_ayahs(item))
                return results
            elif len(raw_data) > 0 and ('number_in_surah' in raw_data[0] or 'text' in raw_data[0] or 'surah' in raw_data[0]):
                edition_meta = {'identifier': fallback_identifier, 'name': fallback_identifier, 'language': 'ar'}
                return [(edition_meta, raw_data)]

        if not isinstance(raw_data, dict):
            raise CommandError("Invalid JSON root: Expected dictionary or list.")

        # Multi-edition format with 'data' array containing verse entries with 'editions' map
        # e.g., sample_quran.json: {"data": [{"surah_number": 1, "number_in_surah": 1, "editions": {"quran-simple": "..."}}]}
        if 'data' in raw_data and isinstance(raw_data['data'], list) and len(raw_data['data']) > 0:
            first_entry = raw_data['data'][0]
            if isinstance(first_entry, dict) and 'editions' in first_entry and isinstance(first_entry['editions'], dict):
                # Multi-edition per ayah map
                grouped_by_edition = {}
                for entry in raw_data['data']:
                    s_num = entry.get('surah_number') or entry.get('surah')
                    a_num = entry.get('number_in_surah') or entry.get('ayah') or entry.get('numberInSurah')
                    g_num = entry.get('global_number') or entry.get('number')
                    juz_num = entry.get('juz')
                    page_num = entry.get('page')
                    audio_val = entry.get('audio_url') or entry.get('audio')

                    for ed_id, text_val in entry['editions'].items():
                        grouped_by_edition.setdefault(ed_id, []).append({
                            'surah_number': s_num,
                            'number_in_surah': a_num,
                            'global_number': g_num,
                            'juz': juz_num,
                            'page': page_num,
                            'text': text_val,
                            'audio_url': audio_val,
                        })

                # Check if editions metadata array exists in root
                ed_meta_dict = {}
                if 'editions' in raw_data and isinstance(raw_data['editions'], list):
                    ed_meta_dict = {e['identifier']: e for e in raw_data['editions']}

                for ed_id, ayahs in grouped_by_edition.items():
                    meta = ed_meta_dict.get(ed_id, {
                        'identifier': ed_id,
                        'name': ed_id,
                        'language': 'ar' if 'quran' in ed_id else ('fa' if 'fa.' in ed_id else 'en'),
                        'type': 'quran' if 'quran' in ed_id else 'translation'
                    })
                    results.append((meta, ayahs))
                return results

        # Format A: Nested data wrapper (Al-Quran Cloud standard)
        data = raw_data.get('data', raw_data)

        # Multi-edition array of objects with 'ayahs' or 'surahs'
        if 'editions' in raw_data and isinstance(raw_data['editions'], list) and 'data' in raw_data:
            editions_meta = {e['identifier']: e for e in raw_data['editions']}
            grouped_ayahs = {}
            for item in raw_data['data']:
                ed_id = item.get('edition') or item.get('edition_id') or fallback_identifier
                grouped_ayahs.setdefault(ed_id, []).append(item)

            for ed_id, ayahs in grouped_ayahs.items():
                meta = editions_meta.get(ed_id, {'identifier': ed_id, 'name': ed_id, 'language': 'ar'})
                results.append((meta, ayahs))
            return results

        # Format B: Nested 'surahs' list or map (e.g. Al-Quran Cloud)
        if isinstance(data, dict) and 'surahs' in data:
            edition_meta = {
                'identifier': data.get('identifier', fallback_identifier),
                'name': data.get('name', data.get('englishName', fallback_identifier)),
                'english_name': data.get('englishName', data.get('name', fallback_identifier)),
                'language': data.get('language', 'ar'),
                'type': data.get('type', 'quran' if data.get('language') == 'ar' else 'translation'),
                'format': data.get('format', 'text'),
                'direction': data.get('direction', 'rtl'),
                'author': data.get('author', ''),
                'is_default': data.get('is_default', False),
                'metadata': data.get('metadata', {}),
            }
            raw_ayahs = []
            surahs_node = data['surahs']
            if isinstance(surahs_node, list):
                for surah in surahs_node:
                    s_num = surah['number']
                    for a in surah.get('ayahs', []):
                        a_copy = dict(a)
                        a_copy['surah_number'] = s_num
                        raw_ayahs.append(a_copy)
            elif isinstance(surahs_node, dict):
                for s_num_str, ayahs in surahs_node.items():
                    for a in ayahs:
                        a_copy = dict(a)
                        a_copy['surah_number'] = int(s_num_str)
                        raw_ayahs.append(a_copy)
            results.append((edition_meta, raw_ayahs))
            return results

        # Format C: Flat 'ayahs' list with 'edition' metadata
        if 'ayahs' in data or 'ayahs' in raw_data:
            edition_meta = raw_data.get('edition') or data.get('edition') or {
                'identifier': fallback_identifier,
                'name': fallback_identifier,
                'language': 'ar'
            }
            ayahs_list = data.get('ayahs') or raw_data.get('ayahs')
            results.append((edition_meta, ayahs_list))
            return results

        raise CommandError(f"Unrecognized Quran JSON dataset schema: keys found: {list(raw_data.keys())}")

    def clean_ayah_text(self, text: str, surah_number: int, ayah_number_in_surah: int, edition_type: str) -> str:
        """
        Cleans ayah text and strips prepended Bismillah in Surahs 2-114 (except #9)
        if the raw dataset erroneously prefixed it to Ayah 1 of the chapter.
        """
        text = str(text).strip()
        if edition_type == 'quran' and surah_number > 1 and surah_number != 9 and ayah_number_in_surah == 1:
            stripped = BISMILLAH_PREFIX_REGEX.sub('', text).strip()
            if stripped:
                return stripped
        return text

    def import_edition_dataset(
        self,
        edition_meta: dict,
        raw_ayahs: list,
        force: bool = False,
        dry_run: bool = False,
        batch_size: int = 1000,
    ):
        """
        Atomically imports or updates an edition and its ayahs.
        Rolls back completely on any validation or database error.
        """
        identifier = str(edition_meta.get('identifier', '')).strip()
        if not identifier:
            raise CommandError("Edition metadata missing required 'identifier' field.")

        if not raw_ayahs:
            raise CommandError(f"No ayahs found for edition '{identifier}'.")

        # Check existing
        if not dry_run:
            existing = QuranEdition.objects.filter(identifier=identifier).first()
            if existing and not force:
                self.stdout.write(self.style.WARNING(
                    f"Edition '{identifier}' already exists. Use --force to overwrite."
                ))
                return

        surahs_cache = {s.number: s for s in QuranSurah.objects.all()} if not dry_run else {}
        ed_type = edition_meta.get('type', 'quran' if edition_meta.get('language') == 'ar' else 'translation')

        ayah_instances = []
        global_counter = 1

        for idx, item in enumerate(raw_ayahs, start=1):
            # Resolve surah number
            s_num = item.get('surah_number') or item.get('surah_id')
            if s_num is None and isinstance(item.get('surah'), dict):
                s_num = item['surah'].get('number')
            elif s_num is None:
                s_num = item.get('surah')

            if not dry_run and (s_num is None or int(s_num) not in surahs_cache):
                raise CommandError(f"Edition '{identifier}': Invalid or missing surah number '{s_num}' at index {idx}")

            surah_obj = surahs_cache[int(s_num)] if not dry_run else None
            num_in_surah = int(item.get('number_in_surah') or item.get('numberInSurah') or item.get('ayah_number') or item.get('ayah') or 1)
            global_num = int(item.get('global_number') or item.get('number') or item.get('id') or global_counter)
            global_counter += 1

            raw_text = item.get('text') or item.get('verse') or item.get('content') or ''
            text = self.clean_ayah_text(raw_text, int(s_num), num_in_surah, ed_type)
            if not text:
                raise CommandError(f"Edition '{identifier}': Empty text at Surah {s_num}:{num_in_surah}")

            normalized_text = normalize_quran_text(text)
            juz = int(item.get('juz') or item.get('juz_number') or (surah_obj.juz_start if surah_obj else 1))
            page = item.get('page') or item.get('page_number') or (surah_obj.page_start if surah_obj else 1)
            manzil = item.get('manzil')
            ruku = item.get('ruku')
            hizb_quarter = item.get('hizbQuarter') or item.get('hizb_quarter')
            sajda = item.get('sajda')
            if isinstance(sajda, bool):
                sajda = {'recommended': True} if sajda else None
            elif not isinstance(sajda, dict):
                sajda = None

            audio_url = item.get('audio') or item.get('audio_url')
            metadata = item.get('metadata', {})

            if not dry_run:
                ayah_instances.append(QuranAyah(
                    edition_id=identifier,
                    surah=surah_obj,
                    number=global_num,
                    number_in_surah=num_in_surah,
                    juz=juz,
                    page=page,
                    manzil=manzil,
                    ruku=ruku,
                    hizb_quarter=hizb_quarter,
                    sajda=sajda,
                    text=text,
                    normalized_text=normalized_text,
                    audio_url=audio_url,
                    metadata=metadata if isinstance(metadata, dict) else {},
                ))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"[DRY-RUN] Validated edition '{identifier}' ({len(raw_ayahs)} ayahs) successfully."
            ))
            return

        # Atomic database insertion
        with transaction.atomic():
            edition, _ = QuranEdition.objects.update_or_create(
                identifier=identifier,
                defaults={
                    'name': edition_meta.get('name', identifier),
                    'english_name': edition_meta.get('english_name') or edition_meta.get('englishName', identifier),
                    'language': edition_meta.get('language', 'ar'),
                    'type': ed_type,
                    'format': edition_meta.get('format', 'text'),
                    'direction': edition_meta.get('direction', 'rtl' if edition_meta.get('language') in ['ar', 'fa', 'ur', 'he'] else 'ltr'),
                    'author': edition_meta.get('author', ''),
                    'is_default': edition_meta.get('is_default', False),
                    'total_ayahs': len(ayah_instances),
                    'metadata': edition_meta.get('metadata', {}),
                }
            )

            # Clear existing ayahs for this edition
            QuranAyah.objects.filter(edition=edition).delete()

            # Bulk insert in chunks
            QuranAyah.objects.bulk_create(ayah_instances, batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully imported edition '{identifier}' ({len(ayah_instances)} ayahs) atomically."
        ))

    def import_from_file(self, file_path: Path, force: bool = False, dry_run: bool = False, batch_size: int = 1000):
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        fallback_id = file_path.stem
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        editions = self.extract_editions_and_ayahs(data, fallback_identifier=fallback_id)
        for meta, ayahs in editions:
            self.import_edition_dataset(meta, ayahs, force=force, dry_run=dry_run, batch_size=batch_size)

    def import_from_directory(self, dir_path: Path, force: bool = False, dry_run: bool = False, batch_size: int = 1000):
        if not dir_path.exists() or not dir_path.is_dir():
            raise CommandError(f"Directory not found: {dir_path}")

        json_files = sorted(dir_path.glob('*.json'))
        if not json_files:
            self.stdout.write(self.style.WARNING(f"No .json files found in {dir_path}"))
            return

        for jf in json_files:
            self.stdout.write(f"Processing {jf.name}...")
            self.import_from_file(jf, force=force, dry_run=dry_run, batch_size=batch_size)

    def import_sample_data(self, data_dir: Path, force: bool = False, dry_run: bool = False, batch_size: int = 1000):
        sample_file = data_dir / 'sample_quran.json'
        if not sample_file.exists():
            raise CommandError(f"Sample Quran fixture not found at {sample_file}")
        self.stdout.write("Importing sample Quran fixture...")
        self.import_from_file(sample_file, force=force, dry_run=dry_run, batch_size=batch_size)

    def import_seed_data(self, data_dir: Path, force: bool = False, dry_run: bool = False, batch_size: int = 1000):
        editions_file = data_dir / 'editions.json'
        if editions_file.exists():
            with open(editions_file, 'r', encoding='utf-8') as f:
                ed_data = json.load(f)
            ed_list = ed_data if isinstance(ed_data, list) else ed_data.get('editions', [])
            if not dry_run:
                with transaction.atomic():
                    for ed in ed_list:
                        QuranEdition.objects.update_or_create(
                            identifier=ed['identifier'],
                            defaults={
                                'name': ed['name'],
                                'english_name': ed.get('english_name') or ed.get('englishName', ed['name']),
                                'language': ed.get('language', 'ar'),
                                'type': ed.get('type', 'quran'),
                                'format': ed.get('format', 'text'),
                                'direction': ed.get('direction', 'rtl'),
                                'author': ed.get('author', ''),
                                'is_default': ed.get('is_default', False),
                                'metadata': ed.get('metadata', {}),
                            }
                        )
            self.stdout.write(self.style.SUCCESS(f"Registered {len(ed_list)} default Quran editions."))

        # Load sample dataset into database
        sample_file = data_dir / 'sample_quran.json'
        if sample_file.exists():
            self.import_from_file(sample_file, force=force, dry_run=dry_run, batch_size=batch_size)
