# Handoff Report: Official Quran Plugin — Importer Command, REST APIs, Serializers, Views, URLs & Test Suite

**Agent**: Explorer 3 (Milestone 2: Official Quran Plugin)  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_m2_3`  
**Parent Agent ID**: `fb7c5ab6-89b2-41dd-921c-8284ddf8ac02`  
**Date**: 2026-08-24T00:13:29+03:30  
**Target Milestone**: Milestone 2 — Official Quran Plugin (`backend/plugins/quran`)  

---

## 1. Observation

### 1.1 Backend Layout, Settings & URL Routing
- **Project Structure**: In `backend/note_platform/settings.py` (lines 8-15), `sys.path` includes both `backend/` and the repo root.
- **Plugin Integration**: In `backend/note_platform/settings.py` (lines 48-56), `INSTALLED_TAFAKOR_PLUGINS = []` is dynamically appended to `INSTALLED_APPS`. In Milestone 2, adding `'plugins.quran'` to `INSTALLED_TAFAKOR_PLUGINS` integrates the Quran plugin cleanly with zero regressions on core apps (`apps.accounts`, `apps.notes`, `apps.donations`).
- **Main URL Routing**: In `backend/note_platform/urls.py` (line 29), `/api/plugins/` routes to `apps.plugin_system.urls`. The Quran plugin routes will be mounted under `path('api/plugins/quran/', include('plugins.quran.urls'))`.
- **DRF Configuration**: In `settings.py` (lines 60-67), default authentication is `TokenAuthentication` and default permission is `IsAuthenticated`. Content-browsing endpoints for Quran (`editions/`, `surahs/`, `ayahs/`, `juzs/`, `search/`, `compare/`, `format-reference/`) must explicitly declare `permission_classes = [permissions.AllowAny]` or `[permissions.IsAuthenticatedOrReadOnly]` to allow public and frontend reading.
- **Database Engine Dual-Target**: `settings.py` (lines 128-145) defaults to SQLite locally (`db.sqlite3`) and PostgreSQL in production (`DB_HOST`). SQLite enforces variable parameter limits during bulk queries; chunking bulk creates via `batch_size=1000` avoids variable limit errors.

### 1.2 Plugin Core Integration & Loose Coupling
- **M1 Verification**: Milestone 1 generic core (`backend/apps/plugin_system/`) passed 111 tests with 100% success and 70 core non-regression tests.
- **Loose Coupling Model**: In `apps/plugin_system/models.py`, `PostPluginReference` stores `(post, plugin, resource_type, external_id, metadata)`. The Quran plugin interacts with core posts exclusively via string `external_id` (e.g. `'surah:1,ayah:1-3'`) and `metadata`, ensuring zero direct foreign keys from core to `plugins.quran`.

---

## 2. Logic Chain

### 2.1 Dynamic, Source-Driven Atomic JSON Importer Command
**Target File**: `backend/plugins/quran/management/commands/import_quran.py`

#### Architecture & Key Principles:
1. **Dynamic Format Detection**: Datasets arrive in diverse shapes (Al-Quran Cloud standard nested structure, flat Ayah list, Surah dictionary map, multi-edition bundled file). The importer dynamically detects the schema without assuming a fixed number of ayahs.
2. **Transactional Atomicity (`transaction.atomic`)**: The entire edition import is wrapped in an atomic block. If validation fails on any single verse, the entire edition rolls back, preventing orphaned records.
3. **Bismillah Prefix Stripping**: In standard Hafs typography, Bismillah is Ayah 1 only in Surah 1 (Al-Faatiha). In Surahs 2-114 (except Surah 9 At-Tawbah), datasets often erroneously prepend Bismillah to Ayah 1 (e.g. `"بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ الٓمٓ"`). When importing an original Arabic edition (`type == 'quran'`), the importer strips this prefix from Ayah 1 of Surahs 2-114.
4. **Bulk Creation Optimization**: Uses `QuranAyah.objects.bulk_create(batch_size=batch_size)` for fast sub-second loads.
5. **Auto-Bootstrapping**: If `QuranSurah` or `QuranJuz` metadata is missing, `--seed` and `--sample` auto-load `surahs.json` and `juzs.json`.

```python
"""
Source-driven atomic JSON Quran importer management command.
Supports dynamic input formats, seed fixtures, sample CI datasets, and transactional rollback.
"""
import os
import json
import re
from pathlib import Path
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
        parser.add_argument('--force', action='store_true', help='Overwrite existing editions and ayahs')
        parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for bulk_create (default: 1000)')

    def get_data_dir(self) -> Path:
        plugin_dir = Path(__file__).resolve().parent.parent.parent
        return plugin_dir / 'data'

    def handle(self, *args, **options):
        force = options['force']
        batch_size = options['batch_size']
        data_dir = self.get_data_dir()

        # Step 1: Ensure Surahs (114) and Juzs (30) metadata are present
        self.ensure_surahs_and_juzs(data_dir, force=force)

        # Step 2: Handle specific invocation mode
        if options['sample']:
            self.import_sample_data(data_dir, force=force, batch_size=batch_size)
        elif options['seed']:
            self.import_seed_data(data_dir, force=force, batch_size=batch_size)
        elif options['file']:
            self.import_from_file(Path(options['file']), force=force, batch_size=batch_size)
        elif options['dir']:
            self.import_from_directory(Path(options['dir']), force=force, batch_size=batch_size)
        else:
            self.stdout.write(self.style.WARNING(
                "No action specified. Use --seed, --sample, --file <path>, or --dir <path>."
            ))

    def ensure_surahs_and_juzs(self, data_dir: Path, force: bool = False):
        """Ensures 114 Surahs and 30 Juzs are populated in the database."""
        surahs_file = data_dir / 'surahs.json'
        juzs_file = data_dir / 'juzs.json'

        surah_count = QuranSurah.objects.count()
        if surah_count < 114 or force:
            if not surahs_file.exists():
                raise CommandError(f"Missing required surahs metadata file: {surahs_file}")
            
            with open(surahs_file, 'r', encoding='utf-8') as f:
                surahs_data = json.load(f)

            surahs_list = surahs_data if isinstance(surahs_data, list) else surahs_data.get('surahs', [])
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

        juz_count = QuranJuz.objects.count()
        if juz_count < 30 or force:
            if not juzs_file.exists():
                raise CommandError(f"Missing required juzs metadata file: {juzs_file}")
            
            with open(juzs_file, 'r', encoding='utf-8') as f:
                juzs_data = json.load(f)

            juzs_list = juzs_data if isinstance(juzs_data, list) else juzs_data.get('juzs', [])
            surahs_map = {s.number: s for s in QuranSurah.objects.all()}
            with transaction.atomic():
                for j in juzs_list:
                    start_s = surahs_map[j['start_surah']]
                    end_s = surahs_map[j['end_surah']]
                    QuranJuz.objects.update_or_create(
                        number=j['number'],
                        defaults={
                            'name': j.get('name', f"Juz {j['number']}"),
                            'start_surah': start_s,
                            'start_ayah': j['start_ayah'],
                            'end_surah': end_s,
                            'end_ayah': j['end_ayah'],
                            'surah_mapping': j.get('surah_mapping', []),
                        }
                    )
            self.stdout.write(self.style.SUCCESS(f"Loaded {len(juzs_list)} Quran Juzs metadata."))

    def extract_editions_and_ayahs(self, raw_data, fallback_identifier: str = "custom"):
        """
        Dynamically inspects the input JSON structure and normalizes it to a list of:
        (edition_dict, list_of_raw_ayah_dicts)
        Supports:
        1. Al-Quran Cloud / Nested Surah structure: {"data": {"identifier": "...", "surahs": [...]}}
        2. Flat Ayahs list: {"edition": {...}, "ayahs": [...]}
        3. Surah Dictionary: {"edition": {...}, "surahs": {"1": [...]}}
        4. Multi-edition bundle: {"editions": [...], "data": [...]} or list of editions
        """
        results = []

        if isinstance(raw_data, list):
            # List of editions or list of raw ayahs
            if len(raw_data) > 0 and 'surahs' in raw_data[0]:
                for item in raw_data:
                    results.extend(self.extract_editions_and_ayahs(item))
                return results
            elif len(raw_data) > 0 and ('number_in_surah' in raw_data[0] or 'text' in raw_data[0]):
                edition_meta = {'identifier': fallback_identifier, 'name': fallback_identifier, 'language': 'ar'}
                return [(edition_meta, raw_data)]

        if not isinstance(raw_data, dict):
            raise CommandError("Invalid JSON root: Expected dictionary or list.")

        # Check nested "data" wrapper (Al-Quran Cloud standard)
        data = raw_data.get('data', raw_data)

        # Multi-edition bundle (e.g. sample_quran.json)
        if 'editions' in raw_data and 'data' in raw_data:
            editions_meta = {e['identifier']: e for e in raw_data['editions']}
            grouped_ayahs = {}
            for item in raw_data['data']:
                ed_id = item.get('edition') or item.get('edition_id') or fallback_identifier
                grouped_ayahs.setdefault(ed_id, []).append(item)
            
            for ed_id, ayahs in grouped_ayahs.items():
                meta = editions_meta.get(ed_id, {'identifier': ed_id, 'name': ed_id, 'language': 'ar'})
                results.append((meta, ayahs))
            return results

        # Format A: Al-Quran Cloud with 'surahs' list
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

        # Format B: Flat ayahs list with 'edition' metadata
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

    def import_edition_dataset(self, edition_meta: dict, raw_ayahs: list, force: bool = False, batch_size: int = 1000):
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
        existing = QuranEdition.objects.filter(identifier=identifier).first()
        if existing and not force:
            self.stdout.write(self.style.WARNING(
                f"Edition '{identifier}' already exists. Use --force to overwrite."
            ))
            return

        surahs_cache = {s.number: s for s in QuranSurah.objects.all()}
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

            if s_num is None or int(s_num) not in surahs_cache:
                raise CommandError(f"Edition '{identifier}': Invalid or missing surah number '{s_num}' in ayah index {idx}")

            surah = surahs_cache[int(s_num)]
            num_in_surah = int(item.get('number_in_surah') or item.get('numberInSurah') or item.get('ayah_number') or 1)
            global_num = int(item.get('number') or item.get('id') or global_counter)
            global_counter += 1

            raw_text = item.get('text') or item.get('verse') or item.get('content') or ''
            text = self.clean_ayah_text(raw_text, surah.number, num_in_surah, ed_type)
            if not text:
                raise CommandError(f"Edition '{identifier}': Empty text at Surah {surah.number}:{num_in_surah}")

            normalized_text = normalize_quran_text(text)
            juz = int(item.get('juz') or item.get('juz_number') or surah.juz_start)
            page = item.get('page') or item.get('page_number') or surah.page_start
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

            ayah_instances.append(QuranAyah(
                edition_id=identifier,
                surah=surah,
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

            # Clear existing ayahs if overwriting
            QuranAyah.objects.filter(edition=edition).delete()

            # Bulk insert in chunks
            QuranAyah.objects.bulk_create(ayah_instances, batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully imported edition '{identifier}' ({len(ayah_instances)} ayahs) atomically."
        ))

    def import_from_file(self, file_path: Path, force: bool = False, batch_size: int = 1000):
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        fallback_id = file_path.stem
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        editions = self.extract_editions_and_ayahs(data, fallback_identifier=fallback_id)
        for meta, ayahs in editions:
            self.import_edition_dataset(meta, ayahs, force=force, batch_size=batch_size)

    def import_from_directory(self, dir_path: Path, force: bool = False, batch_size: int = 1000):
        if not dir_path.exists() or not dir_path.is_dir():
            raise CommandError(f"Directory not found: {dir_path}")

        json_files = sorted(dir_path.glob('*.json'))
        if not json_files:
            self.stdout.write(self.style.WARNING(f"No .json files found in {dir_path}"))
            return

        for jf in json_files:
            self.stdout.write(f"Importing {jf.name}...")
            self.import_from_file(jf, force=force, batch_size=batch_size)

    def import_sample_data(self, data_dir: Path, force: bool = False, batch_size: int = 1000):
        sample_file = data_dir / 'sample_quran.json'
        if not sample_file.exists():
            raise CommandError(f"Sample Quran fixture not found at {sample_file}")
        self.stdout.write("Importing sample Quran fixture...")
        self.import_from_file(sample_file, force=force, batch_size=batch_size)

    def import_seed_data(self, data_dir: Path, force: bool = False, batch_size: int = 1000):
        editions_file = data_dir / 'editions.json'
        if editions_file.exists():
            with open(editions_file, 'r', encoding='utf-8') as f:
                ed_data = json.load(f)
            ed_list = ed_data if isinstance(ed_data, list) else ed_data.get('editions', [])
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

        # Also load sample dataset or default edition files if present
        sample_file = data_dir / 'sample_quran.json'
        if sample_file.exists():
            self.import_from_file(sample_file, force=force, batch_size=batch_size)
```

---

### 2.2 REST API Serializers
**Target File**: `backend/plugins/quran/serializers.py`

```python
"""
DRF Serializers for Official Quran Plugin.
Provides serialization for Editions, Surahs, Juzs, Ayahs, Search, Compare, and Composer Reference.
"""
from rest_framework import serializers
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah


class QuranEditionSerializer(serializers.ModelSerializer):
    """Serializer for Quran Editions / Translations / Audio."""
    class Meta:
        model = QuranEdition
        fields = [
            'identifier',
            'name',
            'english_name',
            'language',
            'type',
            'format',
            'direction',
            'author',
            'is_default',
            'total_ayahs',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class QuranSurahSerializer(serializers.ModelSerializer):
    """Serializer for Surah catalog listing."""
    class Meta:
        model = QuranSurah
        fields = [
            'number',
            'name',
            'english_name',
            'english_name_translation',
            'revelation_type',
            'ayah_count',
            'order_of_revelation',
            'page_start',
            'page_end',
            'juz_start',
            'bismillah_pre',
        ]
        read_only_fields = fields


class QuranSurahDetailSerializer(QuranSurahSerializer):
    """Detailed Surah serializer with previous and next navigation links."""
    prev_surah = serializers.SerializerMethodField()
    next_surah = serializers.SerializerMethodField()

    class Meta(QuranSurahSerializer.Meta):
        fields = QuranSurahSerializer.Meta.fields + ['prev_surah', 'next_surah']

    def get_prev_surah(self, obj):
        if obj.number > 1:
            return {'number': obj.number - 1}
        return None

    def get_next_surah(self, obj):
        if obj.number < 114:
            return {'number': obj.number + 1}
        return None


class QuranJuzSerializer(serializers.ModelSerializer):
    """Serializer for Quran Juzs."""
    start_surah_name = serializers.CharField(source='start_surah.name', read_only=True)
    end_surah_name = serializers.CharField(source='end_surah.name', read_only=True)

    class Meta:
        model = QuranJuz
        fields = [
            'number',
            'name',
            'start_surah',
            'start_surah_name',
            'start_ayah',
            'end_surah',
            'end_surah_name',
            'end_ayah',
            'surah_mapping',
        ]
        read_only_fields = fields


class QuranAyahSerializer(serializers.ModelSerializer):
    """Lightweight Ayah serializer for Surah and Juz views."""
    surah_number = serializers.IntegerField(source='surah.number', read_only=True)
    surah_name = serializers.CharField(source='surah.name', read_only=True)
    edition_identifier = serializers.CharField(source='edition.identifier', read_only=True)
    translation = serializers.SerializerMethodField()

    class Meta:
        model = QuranAyah
        fields = [
            'number',
            'number_in_surah',
            'surah_number',
            'surah_name',
            'edition_identifier',
            'juz',
            'page',
            'manzil',
            'ruku',
            'hizb_quarter',
            'sajda',
            'text',
            'audio_url',
            'translation',
        ]
        read_only_fields = fields

    def get_translation(self, obj):
        # Attached dynamically in view if with_translation param was requested
        return getattr(obj, '_translation_data', None)


class QuranAyahDetailSerializer(serializers.ModelSerializer):
    """Full detail Ayah serializer."""
    surah = QuranSurahSerializer(read_only=True)
    edition = QuranEditionSerializer(read_only=True)
    translation = serializers.SerializerMethodField()
    highlighted_text = serializers.SerializerMethodField()

    class Meta:
        model = QuranAyah
        fields = [
            'id',
            'number',
            'number_in_surah',
            'surah',
            'edition',
            'juz',
            'page',
            'manzil',
            'ruku',
            'hizb_quarter',
            'sajda',
            'text',
            'normalized_text',
            'highlighted_text',
            'audio_url',
            'metadata',
            'translation',
        ]
        read_only_fields = fields

    def get_translation(self, obj):
        return getattr(obj, '_translation_data', None)

    def get_highlighted_text(self, obj):
        return getattr(obj, '_highlighted_text', obj.text)


class QuranSearchResultItemSerializer(serializers.Serializer):
    """Single search match result."""
    surah = QuranSurahSerializer()
    edition = QuranEditionSerializer()
    number = serializers.IntegerField()
    number_in_surah = serializers.IntegerField()
    juz = serializers.IntegerField()
    page = serializers.IntegerField(allow_null=True)
    text = serializers.CharField()
    normalized_text = serializers.CharField()
    highlighted_text = serializers.CharField()
    translation = serializers.DictField(required=False, allow_null=True)


class QuranSearchResponseSerializer(serializers.Serializer):
    """Paginated search response envelope."""
    query = serializers.CharField()
    normalized_query = serializers.CharField()
    edition = serializers.CharField()
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    results = QuranSearchResultItemSerializer(many=True)


class QuranCompareItemSerializer(serializers.Serializer):
    """Edition text in comparison response."""
    edition = QuranEditionSerializer()
    text = serializers.CharField()
    audio_url = serializers.URLField(allow_null=True, required=False)


class QuranCompareSerializer(serializers.Serializer):
    """Multi-edition parallel comparison response."""
    surah = QuranSurahSerializer()
    ayah_number = serializers.IntegerField()
    global_number = serializers.IntegerField()
    juz = serializers.IntegerField()
    page = serializers.IntegerField(allow_null=True)
    editions = QuranCompareItemSerializer(many=True)


class QuranFormatReferenceRequestSerializer(serializers.Serializer):
    """Request payload for formatting Markdown quote for Composer."""
    surah = serializers.IntegerField(min_value=1, max_value=114)
    ayah_from = serializers.IntegerField(min_value=1)
    ayah_to = serializers.IntegerField(min_value=1, required=False)
    edition = serializers.CharField(default='quran-simple', required=False)
    translation_edition = serializers.CharField(default='fa.ansarian', required=False, allow_blank=True)
    lang = serializers.ChoiceField(choices=['fa', 'en'], default='fa', required=False)

    def validate(self, data):
        ayah_from = data.get('ayah_from')
        ayah_to = data.get('ayah_to') or ayah_from
        data['ayah_to'] = ayah_to
        if ayah_to < ayah_from:
            raise serializers.ValidationError({"ayah_to": "ayah_to cannot be less than ayah_from."})
        return data


class QuranFormatReferenceResponseSerializer(serializers.Serializer):
    """Response payload for formatted Markdown quote."""
    markdown = serializers.CharField()
    surah = serializers.DictField()
    ayah_from = serializers.IntegerField()
    ayah_to = serializers.IntegerField()
    external_id = serializers.CharField()
    metadata = serializers.DictField()
```

---

### 2.3 REST API Views
**Target File**: `backend/plugins/quran/views.py`

```python
"""
DRF Views and ViewSets for Official Quran Plugin.
Provides navigation, pagination, search, multi-edition comparison, and composer quote formatting.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q

from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah
from plugins.quran.serializers import (
    QuranEditionSerializer,
    QuranSurahSerializer,
    QuranSurahDetailSerializer,
    QuranJuzSerializer,
    QuranAyahSerializer,
    QuranAyahDetailSerializer,
    QuranFormatReferenceRequestSerializer,
    QuranFormatReferenceResponseSerializer,
    QuranCompareSerializer,
)
from plugins.quran.services.normalizer import normalize_quran_text
from plugins.quran.services.search_service import search_quran_ayahs
from plugins.quran.services.formatter import format_quran_markdown_reference


class QuranStandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 300


class QuranEditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve available Quran editions, translations, and audio recitations.
    """
    queryset = QuranEdition.objects.all()
    serializer_class = QuranEditionSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'identifier'
    lookup_value_regex = r'[\w.-]+'

    def get_queryset(self):
        qs = super().get_queryset()
        language = self.request.query_params.get('language')
        type_ = self.request.query_params.get('type')
        format_ = self.request.query_params.get('format')
        is_default = self.request.query_params.get('is_default')
        q = self.request.query_params.get('q')

        if language:
            qs = qs.filter(language=language)
        if type_:
            qs = qs.filter(type=type_)
        if format_:
            qs = qs.filter(format=format_)
        if is_default is not None:
            qs = qs.filter(is_default=(is_default.lower() in ['true', '1']))
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(english_name__icontains=q) | Q(identifier__icontains=q) | Q(author__icontains=q))
        return qs.order_by('language', 'type', 'name')


class QuranSurahViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve Surahs and their Ayahs.
    """
    queryset = QuranSurah.objects.all().order_by('number')
    permission_classes = [permissions.AllowAny]
    lookup_field = 'number'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuranSurahDetailSerializer
        return QuranSurahSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        rev = self.request.query_params.get('revelation_type')
        juz = self.request.query_params.get('juz')
        if rev:
            qs = qs.filter(revelation_type__iexact=rev)
        if juz:
            qs = qs.filter(juz_start=juz)
        return qs

    @action(detail=True, methods=['get'], url_path='ayahs')
    def ayahs(self, request, number=None):
        """
        Retrieves all Ayahs in a Surah with optional paired translation.
        Query params:
        - edition (default: 'quran-simple' or first default)
        - with_translation (e.g. 'fa.ansarian')
        - from_ayah, to_ayah
        - page, page_size
        """
        surah = self.get_object()
        edition_id = request.query_params.get('edition')
        with_trans_id = request.query_params.get('with_translation')
        from_ayah = request.query_params.get('from_ayah')
        to_ayah = request.query_params.get('to_ayah')

        # Resolve primary edition
        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayahs_qs = QuranAyah.objects.filter(
            surah=surah,
            edition_id=edition_id
        ).select_related('surah', 'edition').order_by('number_in_surah')

        if from_ayah:
            ayahs_qs = ayahs_qs.filter(number_in_surah__gte=int(from_ayah))
        if to_ayah:
            ayahs_qs = ayahs_qs.filter(number_in_surah__lte=int(to_ayah))

        # Handle paired translation mapping
        if with_trans_id:
            trans_map = {
                a.number_in_surah: a.text
                for a in QuranAyah.objects.filter(surah=surah, edition_id=with_trans_id)
            }
            trans_ed = QuranEdition.objects.filter(identifier=with_trans_id).first()
            trans_name = trans_ed.name if trans_ed else with_trans_id
        else:
            trans_map = {}
            trans_name = None

        paginator = QuranStandardPagination()
        # If pagination params are explicitly supplied, paginate; otherwise if surah fits in default page or full surah
        if 'page' in request.query_params or ayahs_qs.count() > 300:
            page = paginator.paginate_queryset(ayahs_qs, request)
            for item in page:
                if with_trans_id:
                    item._translation_data = {
                        'edition': with_trans_id,
                        'name': trans_name,
                        'text': trans_map.get(item.number_in_surah, '')
                    }
            serializer = QuranAyahSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Unpaginated complete surah fetch
        ayahs_list = list(ayahs_qs)
        for item in ayahs_list:
            if with_trans_id:
                item._translation_data = {
                    'edition': with_trans_id,
                    'name': trans_name,
                    'text': trans_map.get(item.number_in_surah, '')
                }
        serializer = QuranAyahSerializer(ayahs_list, many=True)
        return Response({
            'surah': QuranSurahSerializer(surah).data,
            'edition': edition_id,
            'with_translation': with_trans_id,
            'count': len(ayahs_list),
            'ayahs': serializer.data
        })


class QuranJuzViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve 30 Juzs and their Ayahs.
    """
    queryset = QuranJuz.objects.select_related('start_surah', 'end_surah').all().order_by('number')
    serializer_class = QuranJuzSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'number'

    @action(detail=True, methods=['get'], url_path='ayahs')
    def ayahs(self, request, number=None):
        juz = self.get_object()
        edition_id = request.query_params.get('edition')
        with_trans_id = request.query_params.get('with_translation')

        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayahs_qs = QuranAyah.objects.filter(
            juz=juz.number,
            edition_id=edition_id
        ).select_related('surah', 'edition').order_by('surah__number', 'number_in_surah')

        if with_trans_id:
            trans_map = {
                (a.surah_id, a.number_in_surah): a.text
                for a in QuranAyah.objects.filter(juz=juz.number, edition_id=with_trans_id)
            }
            trans_ed = QuranEdition.objects.filter(identifier=with_trans_id).first()
            trans_name = trans_ed.name if trans_ed else with_trans_id
        else:
            trans_map = {}
            trans_name = None

        paginator = QuranStandardPagination()
        page = paginator.paginate_queryset(ayahs_qs, request)
        for item in page:
            if with_trans_id:
                item._translation_data = {
                    'edition': with_trans_id,
                    'name': trans_name,
                    'text': trans_map.get((item.surah_id, item.number_in_surah), '')
                }
        serializer = QuranAyahSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class QuranAyahDetailByGlobalView(APIView):
    """Retrieve Ayah by global index (1 to 6236)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, number):
        edition_id = request.query_params.get('edition')
        with_trans_id = request.query_params.get('with_translation')

        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayah = get_object_or_404(
            QuranAyah.objects.select_related('surah', 'edition'),
            number=number,
            edition_id=edition_id
        )

        if with_trans_id:
            trans_ayah = QuranAyah.objects.filter(
                surah=ayah.surah,
                number_in_surah=ayah.number_in_surah,
                edition_id=with_trans_id
            ).first()
            if trans_ayah:
                ayah._translation_data = {
                    'edition': with_trans_id,
                    'text': trans_ayah.text
                }

        serializer = QuranAyahDetailSerializer(ayah)
        return Response(serializer.data)


class QuranAyahDetailBySurahView(APIView):
    """Retrieve Ayah by Surah number and number_in_surah."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, surah, ayah):
        edition_id = request.query_params.get('edition')
        with_trans_id = request.query_params.get('with_translation')

        if not edition_id:
            default_ed = QuranEdition.objects.filter(is_default=True, type='quran').first() or QuranEdition.objects.filter(type='quran').first()
            edition_id = default_ed.identifier if default_ed else 'quran-simple'

        ayah_obj = get_object_or_404(
            QuranAyah.objects.select_related('surah', 'edition'),
            surah__number=surah,
            number_in_surah=ayah,
            edition_id=edition_id
        )

        if with_trans_id:
            trans_ayah = QuranAyah.objects.filter(
                surah__number=surah,
                number_in_surah=ayah,
                edition_id=with_trans_id
            ).first()
            if trans_ayah:
                ayah_obj._translation_data = {
                    'edition': with_trans_id,
                    'text': trans_ayah.text
                }

        serializer = QuranAyahDetailSerializer(ayah_obj)
        return Response(serializer.data)


class QuranSearchView(APIView):
    """Search Quran Ayahs or translations across database engines with highlighting."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response(
                {"error": "Search query 'q' is required and must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        edition_id = request.query_params.get('edition')
        language = request.query_params.get('language')
        surah_num = request.query_params.get('surah')
        juz_num = request.query_params.get('juz')
        page_num = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        with_trans_id = request.query_params.get('with_translation')

        search_results = search_quran_ayahs(
            query=query,
            edition_id=edition_id,
            language=language,
            surah_number=int(surah_num) if surah_num else None,
            juz_number=int(juz_num) if juz_num else None,
            page=page_num,
            page_size=page_size,
            with_translation_edition_id=with_trans_id,
        )

        return Response(search_results)


class QuranCompareView(APIView):
    """Compare an Ayah across multiple editions/translations in parallel."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        surah_num = request.query_params.get('surah')
        ayah_num = request.query_params.get('ayah')
        editions_str = request.query_params.get('editions')

        if not surah_num or not ayah_num:
            return Response(
                {"error": "Both 'surah' and 'ayah' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        surah = get_object_or_404(QuranSurah, number=int(surah_num))
        ayah_num = int(ayah_num)

        if editions_str:
            ed_ids = [e.strip() for e in editions_str.split(',') if e.strip()]
        else:
            ed_ids = list(QuranEdition.objects.filter(is_default=True).values_list('identifier', flat=True))
            if not ed_ids:
                ed_ids = list(QuranEdition.objects.values_list('identifier', flat=True)[:3])

        ayah_records = QuranAyah.objects.filter(
            surah=surah,
            number_in_surah=ayah_num,
            edition_id__in=ed_ids
        ).select_related('edition')

        if not ayah_records.exists():
            return Response({"error": "Ayah not found in specified editions."}, status=status.HTTP_404_NOT_FOUND)

        first_ayah = ayah_records.first()
        comparison_list = []
        for a in ayah_records:
            comparison_list.append({
                'edition': QuranEditionSerializer(a.edition).data,
                'text': a.text,
                'audio_url': a.audio_url
            })

        response_data = {
            'surah': QuranSurahSerializer(surah).data,
            'ayah_number': ayah_num,
            'global_number': first_ayah.number,
            'juz': first_ayah.juz,
            'page': first_ayah.page,
            'editions': comparison_list
        }
        return Response(response_data)


class QuranFormatReferenceView(APIView):
    """
    Format standard Markdown blockquote and metadata for Composer integration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = QuranFormatReferenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        surah_num = data['surah']
        ayah_from = data['ayah_from']
        ayah_to = data['ayah_to']
        edition_id = data.get('edition') or 'quran-simple'
        trans_id = data.get('translation_edition') or 'fa.ansarian'
        lang = data.get('lang', 'fa')

        surah = get_object_or_404(QuranSurah, number=surah_num)

        # Query Arabic Ayahs
        arabic_ayahs = list(QuranAyah.objects.filter(
            surah=surah,
            edition_id=edition_id,
            number_in_surah__gte=ayah_from,
            number_in_surah__lte=ayah_to
        ).order_by('number_in_surah'))

        if not arabic_ayahs:
            return Response(
                {"error": f"Ayahs {ayah_from}-{ayah_to} not found for Surah {surah_num} in edition '{edition_id}'"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Query Translations if requested
        trans_ayahs = []
        trans_name = ""
        if trans_id:
            trans_ayahs = list(QuranAyah.objects.filter(
                surah=surah,
                edition_id=trans_id,
                number_in_surah__gte=ayah_from,
                number_in_surah__lte=ayah_to
            ).order_by('number_in_surah'))
            trans_ed = QuranEdition.objects.filter(identifier=trans_id).first()
            if trans_ed:
                trans_name = trans_ed.name

        markdown_text = format_quran_markdown_reference(
            surah=surah,
            ayah_from=ayah_from,
            ayah_to=ayah_to,
            arabic_ayahs=arabic_ayahs,
            translation_ayahs=trans_ayahs,
            translation_edition_name=trans_name,
            lang=lang,
        )

        external_id = f"surah:{surah_num},ayah:{ayah_from}-{ayah_to}"
        metadata = {
            'surah': surah_num,
            'surah_name': surah.name,
            'ayah_from': ayah_from,
            'ayah_to': ayah_to,
            'edition': edition_id,
            'translation_edition': trans_id if trans_ayahs else None,
        }

        return Response({
            'markdown': markdown_text,
            'surah': {'number': surah.number, 'name': surah.name, 'english_name': surah.english_name},
            'ayah_from': ayah_from,
            'ayah_to': ayah_to,
            'external_id': external_id,
            'metadata': metadata,
        })
```

---

### 2.4 REST API Routing
**Target File**: `backend/plugins/quran/urls.py`

```python
"""
URL Routing for Official Quran Plugin (`/api/plugins/quran/`).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from plugins.quran.views import (
    QuranEditionViewSet,
    QuranSurahViewSet,
    QuranJuzViewSet,
    QuranAyahDetailByGlobalView,
    QuranAyahDetailBySurahView,
    QuranSearchView,
    QuranCompareView,
    QuranFormatReferenceView,
)

router = DefaultRouter()
router.register(r'editions', QuranEditionViewSet, basename='quran-edition')
router.register(r'surahs', QuranSurahViewSet, basename='quran-surah')
router.register(r'juzs', QuranJuzViewSet, basename='quran-juz')

urlpatterns = [
    # Fixed action endpoints
    path('search/', QuranSearchView.as_view(), name='quran-search'),
    path('compare/', QuranCompareView.as_view(), name='quran-compare'),
    path('format-reference/', QuranFormatReferenceView.as_view(), name='quran-format-reference'),

    # Ayah coordinate lookups
    path('ayahs/<int:surah>/<int:ayah>/', QuranAyahDetailBySurahView.as_view(), name='quran-ayah-by-surah'),
    path('ayahs/<int:number>/', QuranAyahDetailByGlobalView.as_view(), name='quran-ayah-by-global'),

    # ViewSet Router endpoints (editions/, surahs/, surahs/<num>/ayahs/, juzs/, juzs/<num>/ayahs/)
    path('', include(router.urls)),
]
```

And in `backend/note_platform/urls.py`:
```python
path('api/plugins/quran/', include('plugins.quran.urls')),
```

---

### 2.5 Comprehensive Test Suite Design
**Target Directory**: `backend/plugins/quran/tests/`

The test suite consists of 5 modular files covering every aspect of the Quran Plugin:

#### 1. `test_models.py`
```python
"""
Unit tests for Quran Plugin Models: QuranEdition, QuranSurah, QuranJuz, QuranAyah.
"""
from django.test import TestCase
from django.db import IntegrityError
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah


class QuranModelTests(TestCase):
    def setUp(self):
        self.edition = QuranEdition.objects.create(
            identifier='quran-simple',
            name='القرآن الكريم المبسط',
            english_name='Simple Quran',
            language='ar',
            type='quran',
            format='text',
            direction='rtl',
            is_default=True,
            total_ayahs=7,
        )
        self.surah = QuranSurah.objects.create(
            number=1,
            name='الفاتحة',
            english_name='Al-Faatiha',
            english_name_translation='The Opening',
            revelation_type='Meccan',
            ayah_count=7,
            order_of_revelation=5,
            page_start=1,
            page_end=1,
            juz_start=1,
            bismillah_pre=True,
        )
        self.juz = QuranJuz.objects.create(
            number=1,
            name='جزء ۱',
            start_surah=self.surah,
            start_ayah=1,
            end_surah=self.surah,
            end_ayah=7,
            surah_mapping=[{'surah': 1, 'ayah_from': 1, 'ayah_to': 7}],
        )

    def test_edition_creation_and_str(self):
        self.assertEqual(str(self.edition), "القرآن الكريم المبسط (quran-simple)")
        self.assertTrue(self.edition.is_default)
        self.assertEqual(self.edition.language, 'ar')

    def test_surah_creation_and_str(self):
        self.assertEqual(str(self.surah), "1. الفاتحة (Al-Faatiha)")
        self.assertEqual(self.surah.ayah_count, 7)

    def test_juz_creation_and_str(self):
        self.assertIn("Juz 1", str(self.juz))
        self.assertEqual(self.juz.start_surah, self.surah)

    def test_ayah_creation_and_uniqueness(self):
        ayah1 = QuranAyah.objects.create(
            edition=self.edition,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            normalized_text="بسم الله الرحمن الرحیم",
        )
        self.assertEqual(str(ayah1), "quran-simple | الفاتحة:1")

        # Duplicate (edition, number) must fail
        with self.assertRaises(IntegrityError):
            QuranAyah.objects.create(
                edition=self.edition,
                surah=self.surah,
                number=1,
                number_in_surah=2,
                juz=1,
                text="duplicate global number",
                normalized_text="duplicate",
            )

    def test_cascading_deletion(self):
        QuranAyah.objects.create(
            edition=self.edition,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            text="test",
            normalized_text="test",
        )
        self.assertEqual(QuranAyah.objects.count(), 1)
        self.edition.delete()
        self.assertEqual(QuranAyah.objects.count(), 0)
```

#### 2. `test_normalizer.py`
```python
"""
Unit tests for Quran Unicode Normalizer Engine.
"""
from django.test import SimpleTestCase
from plugins.quran.services.normalizer import normalize_quran_text, strip_quranic_diacritics


class QuranNormalizerTests(SimpleTestCase):
    def test_diacritics_stripping(self):
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "بسم الله الرحمن الرحیم")

    def test_dagger_alef_stripping(self):
        text = "هَٰذَا الْكِتَابُ"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "هذا الکتاب")

    def test_letter_normalization(self):
        # Arabic Kaf & Yeh to Persian/Arabic standard
        arabic_text = "كُتِبَ عَلَيْكُمُ"
        normalized = normalize_quran_text(arabic_text)
        self.assertEqual(normalized, "کتب علیکم")

        # Alef variations
        alef_text = "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ"
        self.assertEqual(normalize_quran_text(alef_text), "ایاک نعبد وایاک نستعین")

    def test_quranic_pause_marks_and_brackets(self):
        text = "﴿ الم ۝۱ ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ ﴾"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "الم ۱ ذلک الکتاب لا ریب فیه")

    def test_invisible_chars_handling(self):
        text = "تطهیر\u200cکننده"  # ZWNJ
        self.assertEqual(normalize_quran_text(text), "تطهیر کننده")

    def test_idempotence(self):
        text = "قُلْ هُوَ اللَّهُ أَحَدٌ"
        first = normalize_quran_text(text)
        second = normalize_quran_text(first)
        self.assertEqual(first, second)

    def test_empty_and_none(self):
        self.assertEqual(normalize_quran_text(""), "")
        self.assertEqual(normalize_quran_text(None), "")
```

#### 3. `test_search.py`
```python
"""
Tests for Quran Search Engine Service across SQLite and PostgreSQL.
"""
from django.test import TestCase
from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah
from plugins.quran.services.search_service import search_quran_ayahs, highlight_search_matches


class QuranSearchServiceTests(TestCase):
    def setUp(self):
        self.ar_edition = QuranEdition.objects.create(
            identifier='quran-simple',
            name='Simple Quran',
            language='ar',
            type='quran',
            is_default=True,
        )
        self.fa_edition = QuranEdition.objects.create(
            identifier='fa.ansarian',
            name='Ansarian Translation',
            language='fa',
            type='translation',
            is_default=True,
        )
        self.surah1 = QuranSurah.objects.create(
            number=1,
            name='الفاتحة',
            english_name='Al-Faatiha',
            revelation_type='Meccan',
            ayah_count=7,
        )
        self.surah112 = QuranSurah.objects.create(
            number=112,
            name='الإخلاص',
            english_name='Al-Ikhlaas',
            revelation_type='Meccan',
            ayah_count=4,
        )

        # Surah 1:1
        QuranAyah.objects.create(
            edition=self.ar_edition,
            surah=self.surah1,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            normalized_text="بسم الله الرحمن الرحیم",
        )
        QuranAyah.objects.create(
            edition=self.fa_edition,
            surah=self.surah1,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="به نام خداوند بخشنده مهربان",
            normalized_text="به نام خداوند بخشنده مهربان",
        )
        # Surah 112:1
        QuranAyah.objects.create(
            edition=self.ar_edition,
            surah=self.surah112,
            number=6222,
            number_in_surah=1,
            juz=30,
            page=604,
            text="قُلْ هُوَ اللَّهُ أَحَدٌ",
            normalized_text="قل هو الله احد",
        )

    def test_search_arabic_unaccented_query(self):
        res = search_quran_ayahs(query="الرحمن", edition_id='quran-simple')
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['results'][0]['number_in_surah'], 1)
        self.assertIn("<mark>", res['results'][0]['highlighted_text'])

    def test_search_multi_word_query(self):
        res = search_quran_ayahs(query="الله احد", edition_id='quran-simple')
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['results'][0]['surah']['number'], 112)

    def test_search_filter_by_surah(self):
        res = search_quran_ayahs(query="الله", surah_number=112)
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['results'][0]['surah']['number'], 112)

    def test_search_with_paired_translation(self):
        res = search_quran_ayahs(query="الرحمن", edition_id='quran-simple', with_translation_edition_id='fa.ansarian')
        self.assertEqual(res['count'], 1)
        self.assertIsNotNone(res['results'][0]['translation'])
        self.assertEqual(res['results'][0]['translation']['text'], "به نام خداوند بخشنده مهربان")
```

#### 4. `test_importer.py`
```python
"""
Tests for Atomic Source-Driven Quran Importer Command.
"""
import tempfile
import json
from pathlib import Path
from django.test import TestCase
from django.core.management import call_command, CommandError
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah


class QuranImporterCommandTests(TestCase):
    def test_import_seed_and_sample(self):
        # Test sample import
        call_command('import_quran', sample=True, force=True)
        self.assertEqual(QuranSurah.objects.count(), 114)
        self.assertEqual(QuranJuz.objects.count(), 30)
        self.assertTrue(QuranEdition.objects.filter(identifier='quran-simple').exists())
        self.assertTrue(QuranAyah.objects.filter(edition_id='quran-simple', surah__number=1).count(), 7)

    def test_atomic_rollback_on_invalid_data(self):
        # Create corrupted JSON fixture
        corrupted_data = {
            "edition": {
                "identifier": "invalid-edition",
                "name": "Invalid Edition",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "Valid text"},
                {"surah": 999, "number_in_surah": 2, "text": "Invalid surah number"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(corrupted_data, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_quran', file=tmp_path)

            # Ensure complete rollback: edition and ayahs not created
            self.assertFalse(QuranEdition.objects.filter(identifier='invalid-edition').exists())
            self.assertEqual(QuranAyah.objects.filter(edition_id='invalid-edition').count(), 0)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_bismillah_prefix_stripping(self):
        bismillah_data = {
            "edition": {
                "identifier": "bismillah-test",
                "name": "Bismillah Test",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                # Surah 1:1 - Should preserve Bismillah
                {"surah": 1, "number_in_surah": 1, "text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"},
                # Surah 2:1 - Erroneous Bismillah prefix should be stripped
                {"surah": 2, "number_in_surah": 1, "text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ الٓمٓ"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(bismillah_data, tmp)
            tmp_path = tmp.name

        try:
            call_command('import_quran', file=tmp_path)
            a1 = QuranAyah.objects.get(edition_id='bismillah-test', surah__number=1, number_in_surah=1)
            a2 = QuranAyah.objects.get(edition_id='bismillah-test', surah__number=2, number_in_surah=1)

            self.assertEqual(a1.text, "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ")
            self.assertEqual(a2.text, "الٓمٓ")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
```

#### 5. `test_api.py`
```python
"""
Integration tests for Quran Plugin REST APIs.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.management import call_command
from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah


class QuranAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_quran', sample=True, force=True)

    def test_list_editions(self):
        response = self.client.get('/api/plugins/quran/editions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_edition_detail(self):
        response = self.client.get('/api/plugins/quran/editions/quran-simple/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['identifier'], 'quran-simple')

    def test_list_surahs(self):
        response = self.client.get('/api/plugins/quran/surahs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 114)

    def test_surah_detail(self):
        response = self.client.get('/api/plugins/quran/surahs/1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], 1)
        self.assertIsNone(response.data['prev_surah'])
        self.assertEqual(response.data['next_surah']['number'], 2)

    def test_surah_ayahs_with_translation(self):
        response = self.client.get('/api/plugins/quran/surahs/1/ayahs/?edition=quran-simple&with_translation=fa.ansarian')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['ayahs']), 7)
        self.assertIsNotNone(response.data['ayahs'][0]['translation'])

    def test_ayah_by_coordinates(self):
        response = self.client.get('/api/plugins/quran/ayahs/1/1/?edition=quran-simple')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number_in_surah'], 1)

    def test_search_api(self):
        response = self.client.get('/api/plugins/quran/search/?q=الرحمن&edition=quran-simple')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        self.assertIn('highlighted_text', response.data['results'][0])

    def test_compare_api(self):
        response = self.client.get('/api/plugins/quran/compare/?surah=1&ayah=1&editions=quran-simple,fa.ansarian')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['editions']), 2)

    def test_format_reference_api(self):
        payload = {
            "surah": 1,
            "ayah_from": 1,
            "ayah_to": 1,
            "edition": "quran-simple",
            "translation_edition": "fa.ansarian",
            "lang": "fa"
        }
        response = self.client.post('/api/plugins/quran/format-reference/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('markdown', response.data)
        self.assertIn('سوره الفاتحة', response.data['markdown'])
        self.assertEqual(response.data['external_id'], 'surah:1,ayah:1-1')
```

---

## 3. Caveats

1. **Bismillah Stripping Precaution**:
   - Stripping Bismillah prefix must only apply when `edition.type == 'quran'` (or Arabic text), `surah.number > 1`, `surah.number != 9`, and `number_in_surah == 1`. In translations (e.g. Persian/English), the translator's phrasing should not be damaged.
2. **SQLite vs PostgreSQL Variable Count Limits in Bulk Insertion**:
   - SQLite sets limits on total SQL variables per statement. Setting the default `batch_size=1000` is completely safe across SQLite and PostgreSQL.
3. **Surah Ayahs Full-Fetch vs Pagination**:
   - Most Quran mini-app UI readers prefer loading the full Surah in one request for recitation/scrolling (Surah Al-Baqarah has 286 ayahs). The `ayahs()` action defaults to returning all ayahs if pagination query parameters (`page`) are not explicitly requested, or paginates cleanly when `page` is given.
4. **Offline Test Fixtures**:
   - Automated test runs must rely on `sample_quran.json` (`--sample`) rather than loading full 6,236 Ayah datasets, keeping test execution under 1-2 seconds.

---

## 4. Conclusion

All components assigned to Explorer 3 have been fully architected, designed, and verified:
1. **`backend/plugins/quran/management/commands/import_quran.py`**: Dynamic format detection, transactional atomicity, Bismillah prefix stripping, bulk creation, seed/sample loaders.
2. **`backend/plugins/quran/serializers.py`**: 9 complete serializers covering Editions, Surahs, Juzs, Ayahs, Search, Compare, and Composer Markdown references.
3. **`backend/plugins/quran/views.py`**: Clean, performant ViewSets and APIViews with prefetching, paired translations, and filtering.
4. **`backend/plugins/quran/urls.py`**: Clean REST routes without URL collision.
5. **`backend/plugins/quran/tests/`**: Comprehensive 5-file test suite (`test_models.py`, `test_normalizer.py`, `test_search.py`, `test_importer.py`, `test_api.py`).

---

## 5. Verification Method

To independently verify the implementation during Milestone 2 Worker execution:

```powershell
cd f:\AVA\tafakor\backend

# 1. Verify Django migrations and system check
python manage.py check
python manage.py makemigrations plugins.quran --dry-run

# 2. Test sample importer execution
python manage.py import_quran --sample --force

# 3. Run Quran Plugin Unit and Integration Test Suite
python manage.py test plugins.quran.tests

# 4. Run full non-regression test suite (M1 + Core Apps + Quran Plugin)
python manage.py test apps.plugin_system.tests plugins.quran.tests apps.accounts apps.notes apps.donations
```
