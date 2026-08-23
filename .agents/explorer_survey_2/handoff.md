# Handoff Report: Official Quran Plugin & Data Importer (R2 Survey & Architectural Design)

## 1. Observation

### 1.1 Backend Layout & App Loading
- **Django Settings**: In `backend/note_platform/settings.py` (lines 10-15), the sys.path is dynamically configured:
  ```python
  BASE_DIR = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(BASE_DIR.parent))
  sys.path.insert(0, str(BASE_DIR))
  ```
  Since `backend/` is on `sys.path`, placing plugins under `backend/plugins/quran` allows referencing the app as `plugins.quran` or `plugins.quran.apps.QuranConfig`.
- **Installed Apps & Zero-Breaking Isolation**: Currently `INSTALLED_APPS` (lines 28-43 of `settings.py`) lists core apps (`apps.accounts`, `apps.notes`, `apps.donations`). In R1/R2, plugins can be registered cleanly via `INSTALLED_TAFAKOR_PLUGINS = ['plugins.quran']` merged into `INSTALLED_APPS = [*CORE_APPS, *INSTALLED_TAFAKOR_PLUGINS]`. If `INSTALLED_TAFAKOR_PLUGINS = []`, zero errors occur because core apps have no direct imports or ForeignKey ties to `plugins.quran`.
- **Existing Text Normalization in Core**: In `backend/apps/notes/models.py` (lines 35-58), a basic `normalize_persian_text` function normalizes Persian/Arabic letters for post content hash matching (`ك` -> `ک`, `ي`/`ئ` -> `ی`, `إ`/`أ`/`آ` -> `ا`). However, Quranic Arabic text contains extensive diacritics (harakat/tashkeel), dagger alefs (`\u0670`), Quranic stop marks, and special glyphs that require a dedicated, comprehensive Quranic Unicode normalizer.

### 1.2 Database & Environment
- **Dual Database Target**: In `backend/note_platform/settings.py` (lines 115-133), the system uses PostgreSQL if `DB_HOST` is present (Docker/Production) and defaults to SQLite (`db.sqlite3`) for local development and unit tests.
- **Search Engine Requirement**: The search mechanism cannot rely solely on PostgreSQL-specific extensions (e.g. `pg_trgm` or `unaccent` dictionary) because unit tests and developer environments run on SQLite. Storing a pre-computed `normalized_text` field on each `QuranAyah` provides identical, sub-millisecond search performance across both SQLite (`normalized_text__icontains` / `__contains`) and PostgreSQL.

### 1.3 Test Suite & Isolation
- **Existing Tests**: 35 core integration and unit tests run via `pytest` (configured in `pytest.ini` with `--reuse-db -v --cov=backend`).
- **Zero Regression**: R2 must include isolated unit/integration tests (`backend/plugins/quran/tests/`) covering models, normalization, importer, and APIs without mutating or interfering with existing notes/donations/accounts tests.

---

## 2. Logic Chain

### 2.1 Directory Structure & Plugin Packaging
The Quran plugin will reside in `backend/plugins/quran/` structured as follows:

```
backend/plugins/
├── __init__.py
└── quran/
    ├── __init__.py
    ├── apps.py                  # QuranConfig(AppConfig)
    ├── manifest.json            # Plugin manifest conforming to R1 plugin standard
    ├── models.py                # QuranEdition, QuranSurah, QuranJuz, QuranAyah
    ├── serializers.py           # DRF Serializers
    ├── views.py                 # DRF ViewSets & API Views
    ├── urls.py                  # API endpoints (/editions/, /surahs/, /ayahs/, /juzs/, /search/, /compare/, /format-reference/)
    ├── services/
    │   ├── __init__.py
    │   ├── normalizer.py        # Arabic/Persian Unicode diacritic stripping & char normalization
    │   ├── search_service.py    # Cross-database substring & token query engine
    │   └── formatter.py         # Markdown quote and reference builder for Composer
    ├── management/
    │   ├── __init__.py
    │   └── commands/
    │       ├── __init__.py
    │       └── import_quran.py  # Source-driven atomic JSON importer command
    ├── data/                    # Bundled seed fixtures for offline testing & bootstrapping
    │   ├── editions.json        # Default editions registry metadata
    │   ├── surahs.json          # 114 Surahs metadata (names, ayah count, pages, juz)
    │   ├── juzs.json            # 30 Juzs boundary & mapping metadata
    │   ├── sample_quran.json    # Minimal test fixtures (Surahs 1, 112-114) for fast CI runs
    │   └── default_editions/    # (Optional) Pre-bundled full datasets (Simple Arabic, Ansarian, Sahih)
    ├── migrations/
    │   ├── __init__.py
    │   └── 0001_initial.py
    └── tests/
        ├── __init__.py
        ├── test_models.py
        ├── test_normalizer.py
        ├── test_importer.py
        └── test_api.py
```

### 2.2 Multi-Edition Data Models (`backend/plugins/quran/models.py`)

The data architecture completely decouples Surah metadata (static 114 chapters) from Editions (Arabic scripts, Persian/English translations, Tafsirs, Audio recitations).

```python
from django.db import models


class QuranEdition(models.Model):
    """
    Represents a specific Quran edition, translation, transliteration, or recitation.
    """
    TYPE_CHOICES = [
        ('quran', 'Original Quran Text'),
        ('translation', 'Translation'),
        ('transliteration', 'Transliteration'),
        ('tafsir', 'Tafsir / Commentary'),
        ('audio', 'Audio Recitation'),
    ]
    FORMAT_CHOICES = [
        ('text', 'Text'),
        ('audio', 'Audio'),
    ]
    DIRECTION_CHOICES = [
        ('rtl', 'Right-to-Left (RTL)'),
        ('ltr', 'Left-to-Right (LTR)'),
    ]

    identifier = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique slug (e.g. 'quran-simple', 'fa.ansarian', 'en.sahih')"
    )
    name = models.CharField(max_length=150, help_text="Localized name (e.g. 'ترجمه انصاریان')")
    english_name = models.CharField(max_length=150, help_text="English name (e.g. 'Ansarian Translation')")
    language = models.CharField(max_length=10, db_index=True, help_text="ISO 639-1 code ('ar', 'fa', 'en', etc.)")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='translation', db_index=True)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='text')
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES, default='rtl')
    author = models.CharField(max_length=150, blank=True, default='')
    is_default = models.BooleanField(default=False, db_index=True, help_text="Default edition for language/type")
    total_ayahs = models.IntegerField(default=6236)
    metadata = models.JSONField(default=dict, blank=True, help_text="Source url, license, audio bitrate, reciter details")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['language', 'type', 'name']
        verbose_name = 'Quran Edition'
        verbose_name_plural = 'Quran Editions'

    def __str__(self):
        return f"{self.name} ({self.identifier})"


class QuranSurah(models.Model):
    """
    Represents the 114 Surahs of the Holy Quran.
    """
    REVELATION_CHOICES = [
        ('Meccan', 'Meccan (مکی)'),
        ('Medinan', 'Medinan (مدنی)'),
    ]

    number = models.IntegerField(primary_key=True, help_text="Surah Number (1 to 114)")
    name = models.CharField(max_length=100, help_text="Arabic name (e.g. 'الفاتحة')")
    english_name = models.CharField(max_length=100, help_text="Transliterated name (e.g. 'Al-Faatiha')")
    english_name_translation = models.CharField(max_length=150, help_text="English translation (e.g. 'The Opening')")
    revelation_type = models.CharField(max_length=20, choices=REVELATION_CHOICES, db_index=True)
    ayah_count = models.IntegerField(help_text="Total number of Ayahs in this Surah")
    order_of_revelation = models.IntegerField(null=True, blank=True)
    page_start = models.IntegerField(null=True, blank=True, help_text="Starting page in standard 604-page Madinah Mushaf")
    page_end = models.IntegerField(null=True, blank=True)
    juz_start = models.IntegerField(default=1)
    bismillah_pre = models.BooleanField(
        default=True,
        help_text="True if Bismillah is displayed before Surah (False for Surah At-Tawbah #9)"
    )

    class Meta:
        ordering = ['number']
        verbose_name = 'Quran Surah'
        verbose_name_plural = 'Quran Surahs'

    def __str__(self):
        return f"{self.number}. {self.name} ({self.english_name})"


class QuranJuz(models.Model):
    """
    Represents the 30 Juzs (parts) of the Quran and their Surah boundary mappings.
    """
    number = models.IntegerField(primary_key=True, help_text="Juz Number (1 to 30)")
    name = models.CharField(max_length=100, blank=True, default='', help_text="e.g. 'جزء اول', 'جزء ۳۰ (عمّ)'")
    start_surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='juz_starts')
    start_ayah = models.IntegerField()
    end_surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='juz_ends')
    end_ayah = models.IntegerField()
    surah_mapping = models.JSONField(
        default=list,
        blank=True,
        help_text="List of surah segments included: [{'surah': 1, 'ayah_from': 1, 'ayah_to': 7}, ...]"
    )

    class Meta:
        ordering = ['number']
        verbose_name = 'Quran Juz'
        verbose_name_plural = 'Quran Juzs'

    def __str__(self):
        return f"Juz {self.number} ({self.name or self.number})"


class QuranAyah(models.Model):
    """
    Represents an individual Ayah for a specific Edition.
    """
    id = models.BigAutoField(primary_key=True)
    edition = models.ForeignKey(QuranEdition, on_delete=models.CASCADE, related_name='ayahs', db_index=True)
    surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='ayahs', db_index=True)
    number = models.IntegerField(db_index=True, help_text="Global Ayah number across the Quran (1 to 6236)")
    number_in_surah = models.IntegerField(db_index=True, help_text="Ayah number within the Surah (1 to surah.ayah_count)")
    juz = models.IntegerField(db_index=True, help_text="Juz number (1 to 30)")
    manzil = models.IntegerField(null=True, blank=True, help_text="Manzil (1 to 7)")
    page = models.IntegerField(null=True, blank=True, db_index=True, help_text="Standard Madinah Mushaf page (1 to 604)")
    ruku = models.IntegerField(null=True, blank=True)
    hizb_quarter = models.IntegerField(null=True, blank=True, help_text="Hizb quarter (1 to 240)")
    sajda = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Sajda details (e.g. {'recommended': true, 'obligatory': false} or null)"
    )
    text = models.TextField(help_text="Authentic original text with full diacritics / Uthmani script / translation")
    normalized_text = models.TextField(
        blank=True,
        db_index=True,
        help_text="Diacritic-stripped and standardized text for fast search indexing"
    )
    audio_url = models.URLField(max_length=500, blank=True, null=True, help_text="Ayah-specific audio stream URL")
    metadata = models.JSONField(default=dict, blank=True, help_text="Footnotes, audio offsets, word-by-word data")

    class Meta:
        ordering = ['surah', 'number_in_surah']
        unique_together = [
            ('edition', 'number'),
            ('edition', 'surah', 'number_in_surah')
        ]
        indexes = [
            models.Index(fields=['edition', 'surah', 'number_in_surah']),
            models.Index(fields=['edition', 'juz']),
            models.Index(fields=['edition', 'page']),
            models.Index(fields=['surah', 'number_in_surah']),
            models.Index(fields=['edition', 'normalized_text']),
        ]
        verbose_name = 'Quran Ayah'
        verbose_name_plural = 'Quran Ayahs'

    def __str__(self):
        return f"{self.edition.identifier} | {self.surah.name}:{self.number_in_surah}"
```

### 2.3 Unicode Text Normalization Engine (`backend/plugins/quran/services/normalizer.py`)

A comprehensive, deterministic Unicode normalizer for Arabic and Persian Quranic text:

```python
import re
import unicodedata

# Unicode character classes for Quranic diacritics, signs, and annotations
# Includes: Tashkeel (Fathah, Dammah, Kasrah, Sukun, Shaddah, Tanwin),
# Small High Signs (Sajda, Rub el Hizb, Waqf stops), Dagger Alef, Madda
QURANIC_DIACRITICS_REGEX = re.compile(
    r'[\u0610-\u061A'  # Quranic annotations
    r'\u064B-\u065F'  # Harakat & Shaddah & Maddah
    r'\u0670'          # Superscript/Dagger Alef (ٰ)
    r'\u06D6-\u06DC'  # Quranic Stop Marks (صلے، قلے، ج، لا، etc.)
    r'\u06DF-\u06E8'  # Quranic special pause/sajda symbols
    r'\u06EA-\u06ED]'  # Extra Quranic signs
)

CHAR_MAPPINGS = {
    # Alef normalization (Standardize to bare Alef 'ا')
    'أ': 'ا',
    'إ': 'ا',
    'آ': 'ا',
    'ٱ': 'ا',  # Alef Wasla
    'ٲ': 'ا',
    'ٳ': 'ا',
    'ٵ': 'ا',

    # Yeh / Yaa normalization (Standardize to unified Persian/Arabic Yeh 'ی')
    'ي': 'ی',  # Arabic Yaa (with dots)
    'ى': 'ی',  # Alef Maksura
    'ئ': 'ی',  # Yeh with Hamza
    'ؽ': 'ی',
    'ؾ': 'ی',
    'ؿ': 'ی',
    'ے': 'ی',  # Urdu Bari Ye

    # Kaf normalization (Standardize to Persian/Arabic 'ک')
    'ك': 'ک',
    'ګ': 'ک',
    'ڬ': 'ک',
    'ڭ': 'ک',
    'ڮ': 'ک',

    # Waw normalization
    'ؤ': 'و',  # Waw with Hamza

    # Teh Marbuta & Heh normalization
    'ة': 'ه',
    'ۀ': 'ه',
    'ۃ': 'ه',

    # Tatweel / Kashida
    'ـ': '',

    # Zero-width formatting characters
    '\u200c': ' ',  # ZWNJ -> space
    '\u200d': '',   # ZWJ -> remove
    '\u200e': '',   # LRM
    '\u200f': '',   # RLM
    '\ufeff': '',   # BOM

    # Quranic brackets, quotes & verse end ornaments
    '﴿': '',
    '﴾': '',
    '«': '',
    '»': '',
    '۝': '',
    '۞': '',
    '۩': '',
}


def normalize_quran_text(text: str) -> str:
    """
    Transforms Arabic or Persian Quranic text into a canonical searchable form:
    1. Normalizes Unicode decomposition (NFKD).
    2. Strips all Harakat, Tashkeel, Dagger Alefs, and Quranic stop marks.
    3. Maps all Alef/Yeh/Kaf/Waw/Teh-Marbuta variants to single canonical letters.
    4. Removes Tatweel, punctuation, and cleans extra whitespace.
    """
    if not text:
        return ""

    # Step 1: Normalize unicode
    text = unicodedata.normalize('NFKD', text)

    # Step 2: Remove diacritics & Quranic symbols
    text = QURANIC_DIACRITICS_REGEX.sub('', text)

    # Step 3: Replace character variations
    for old, new in CHAR_MAPPINGS.items():
        text = text.replace(old, new)

    # Step 4: Remove punctuation, numbers, non-letter symbols (keeping Arabic/Persian/Latin letters)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

    # Step 5: Collapse multiple whitespaces and trim
    text = re.sub(r'\s+', ' ', text).strip().lower()

    return text
```

### 2.4 Search Engine Architecture (`backend/plugins/quran/services/search_service.py`)

Search works identically on SQLite and PostgreSQL:
1. The user's search query `q` is passed through `normalize_quran_text(q)` to produce `normalized_q`.
2. A single SQL query is executed against `QuranAyah.objects.filter(...)`:
   - If single term / exact phrase: `normalized_text__contains=normalized_q`.
   - If multi-term: splits `normalized_q` into words and builds an `AND` combination `Q(normalized_text__contains=word_1) & Q(normalized_text__contains=word_2)`.
3. Results are returned with pagination, surah info, and authentic `ayah.text` for display and copying.
4. **Highlighting**: Generates `highlighted_text` by matching tokens in the original string without stripping original diacritics.

### 2.5 Source-Driven Atomic JSON Importer (`backend/plugins/quran/management/commands/import_quran.py`)

**CLI Command Options**:
- `python manage.py import_quran --seed`: Bootstraps default metadata (114 Surahs, 30 Juzs) and bundled sample editions.
- `python manage.py import_quran --file <path>`: Imports an edition from a local JSON file.
- `python manage.py import_quran --dir <path>`: Imports all `.json` edition files in a folder.
- `python manage.py import_quran --edition <identifier>`: Fetches and imports a verified official remote edition by identifier.
- `python manage.py import_quran --sample`: Imports a lightweight fixture (Surahs 1, 112, 113, 114) for fast test execution in CI.
- `python manage.py import_quran --force`: Overwrites/updates existing records.
- `python manage.py import_quran --batch-size 1000`: Configurable bulk insert batch size.

**Dynamic Dataset Format Handling (No hardcoded count assumptions)**:
The importer supports multiple industry JSON formats dynamically:
1. **Al-Quran Cloud Standard Format**: JSON containing `{"data": {"identifier": "...", "surahs": [{"number": 1, "ayahs": [...]}]}}`.
2. **Flat Ayah List Format**: JSON containing `{"edition": {...}, "ayahs": [{"surah": 1, "number_in_surah": 1, "text": "..."}]}`.
3. **Surah Dictionary Format**: JSON mapping surah numbers directly to lists of ayahs.

**Transactional Atomicity & Validation Pipeline**:
```python
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah
from plugins.quran.services.normalizer import normalize_quran_text


class Command(BaseCommand):
    help = "Source-driven atomic Quran dataset importer."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to JSON edition file')
        parser.add_argument('--dir', type=str, help='Path to directory containing JSON edition files')
        parser.add_argument('--seed', action='store_true', help='Import bundled surahs, juzs, and seed editions')
        parser.add_argument('--sample', action='store_true', help='Import small sample dataset for tests')
        parser.add_argument('--force', action='store_true', help='Overwrite existing editions')
        parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for bulk insertion')

    def handle(self, *args, **options):
        # 1. Ensure 114 Surahs and 30 Juzs metadata are populated
        self.ensure_surahs_and_juzs(force=options['force'])

        # 2. Process requested dataset sources
        if options['sample']:
            self.import_sample_data(force=options['force'])
        elif options['seed']:
            self.import_seed_data(force=options['force'])
        elif options['file']:
            self.import_file(options['file'], force=options['force'], batch_size=options['batch_size'])
        elif options['dir']:
            self.import_dir(options['dir'], force=options['force'], batch_size=options['batch_size'])

    def import_edition_dataset(self, data, force=False, batch_size=1000):
        # Step 1: Validate Schema & Header
        edition_meta = self.extract_and_validate_edition_metadata(data)
        identifier = edition_meta['identifier']

        # Step 2: Extract Ayahs List without assuming fixed count
        raw_ayahs = self.extract_raw_ayahs(data)
        if not raw_ayahs:
            raise CommandError(f"No ayahs found in dataset for edition '{identifier}'")

        # Step 3: Parse and validate each ayah
        surahs_cache = {s.number: s for s in QuranSurah.objects.all()}
        ayah_instances = []
        
        for item in raw_ayahs:
            surah_num = int(item.get('surah_number') or item.get('surah', {}).get('number') or item.get('surah'))
            if surah_num not in surahs_cache:
                raise CommandError(f"Invalid surah number {surah_num} in dataset")
            
            surah = surahs_cache[surah_num]
            num_in_surah = int(item.get('number_in_surah') or item.get('numberInSurah') or 1)
            global_num = int(item.get('number') or (surah_num * 1000 + num_in_surah))
            text = str(item.get('text', '')).strip()
            
            if not text:
                raise CommandError(f"Empty text in Ayah {surah_num}:{num_in_surah}")

            normalized = normalize_quran_text(text)
            juz = int(item.get('juz') or surah.juz_start)
            page = item.get('page') or surah.page_start
            manzil = item.get('manzil')
            ruku = item.get('ruku')
            hizb_quarter = item.get('hizbQuarter') or item.get('hizb_quarter')
            sajda = item.get('sajda')
            audio_url = item.get('audio') or item.get('audio_url')

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
                sajda=sajda if isinstance(sajda, dict) else ({"recommended": True} if sajda else None),
                text=text,
                normalized_text=normalized,
                audio_url=audio_url,
            ))

        # Step 4: Transactional Atomic Insertion
        with transaction.atomic():
            edition, _ = QuranEdition.objects.update_or_create(
                identifier=identifier,
                defaults={
                    'name': edition_meta['name'],
                    'english_name': edition_meta.get('english_name', edition_meta['name']),
                    'language': edition_meta['language'],
                    'type': edition_meta.get('type', 'translation'),
                    'format': edition_meta.get('format', 'text'),
                    'direction': edition_meta.get('direction', 'rtl'),
                    'author': edition_meta.get('author', ''),
                    'is_default': edition_meta.get('is_default', False),
                    'total_ayahs': len(ayah_instances),
                    'metadata': edition_meta.get('metadata', {}),
                }
            )

            # Clear existing ayahs for this edition if force updating
            QuranAyah.objects.filter(edition=edition).delete()

            # Bulk insert ayahs in efficient chunks
            QuranAyah.objects.bulk_create(ayah_instances, batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully imported edition '{identifier}' ({len(ayah_instances)} ayahs) atomically."
        ))
```

### 2.6 REST API Specifications (`backend/plugins/quran/urls.py` & `views.py`)

Base prefix: `/api/plugins/quran/`

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/api/plugins/quran/editions/` | `language`, `type`, `format` | List all available editions & metadata |
| `GET` | `/api/plugins/quran/editions/<identifier>/` | - | Retrieve single edition details |
| `GET` | `/api/plugins/quran/surahs/` | - | List all 114 Surahs with metadata |
| `GET` | `/api/plugins/quran/surahs/<int:number>/` | - | Get specific Surah details |
| `GET` | `/api/plugins/quran/surahs/<int:number>/ayahs/` | `edition`, `with_translation`, `page`, `page_size`, `from_ayah`, `to_ayah` | Paginated Ayahs for a Surah with optional paired translation |
| `GET` | `/api/plugins/quran/ayahs/<int:global_number>/` | `edition`, `with_translation` | Fetch single Ayah by global index (1..6236) |
| `GET` | `/api/plugins/quran/ayahs/<int:surah>/<int:ayah>/` | `edition`, `with_translation` | Fetch single Ayah by Surah and Ayah number |
| `GET` | `/api/plugins/quran/juzs/` | - | List all 30 Juz with surah span mappings |
| `GET` | `/api/plugins/quran/juzs/<int:number>/` | - | Get single Juz metadata and boundary info |
| `GET` | `/api/plugins/quran/juzs/<int:number>/ayahs/` | `edition`, `page`, `page_size` | Get all Ayahs in a specific Juz |
| `GET` | `/api/plugins/quran/search/` | `q` (required), `edition`, `language`, `surah`, `juz`, `page`, `page_size` | Normalized search across Quran text or translations |
| `GET` | `/api/plugins/quran/compare/` | `surah`, `ayah`, `editions` (comma-separated) | Parallel multi-edition / multi-translation compare |
| `POST`| `/api/plugins/quran/format-reference/` | Body: `{"surah": 1, "ayah_from": 1, "ayah_to": 3, "editions": ["quran-simple", "fa.ansarian"]}` | Generates formatted Markdown quote for Composer |

**Example Search Response (`/api/plugins/quran/search/?q=الرحمن`)**:
```json
{
  "query": "الرحمن",
  "normalized_query": "الرحمن",
  "edition": "quran-simple",
  "count": 57,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "results": [
    {
      "surah": {
        "number": 1,
        "name": "الفاتحة",
        "english_name": "Al-Faatiha",
        "english_name_translation": "The Opening"
      },
      "number": 1,
      "number_in_surah": 1,
      "juz": 1,
      "page": 1,
      "text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
      "normalized_text": "بسم الله الرحمن الرحیم",
      "highlighted_text": "بِسْمِ ٱللَّهِ <mark>ٱلرَّحْمَٰنِ</mark> ٱلرَّحِيمِ",
      "translation": {
        "edition": "fa.ansarian",
        "text": "به نام خداوند بخشنده مهربان"
      }
    }
  ]
}
```

### 2.7 Composer Reference Integration & Zero-Breaking Contract

When inserting a Quran reference from the frontend Composer Action:
1. The user selects a Surah, Ayah range (e.g. Surah 1:1-3), and preferred translation (e.g. `fa.ansarian`).
2. The plugin formats standard Markdown text:
   ```markdown
   > ﴿بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ﴾
   > *به نام خداوند بخشنده مهربان*
   > — **سوره الفاتحة (۱:۱)**
   ```
3. This text is appended directly to `TopicMessageInput.vue` `text.value`.
4. Optionally, a reference record is created in `PostPluginReference` (R1 core):
   - `plugin`: `'quran'`
   - `post_id`: `<post_id>`
   - `external_id`: `'surah:1,ayah:1-1'`
   - `metadata`: `{"surah": 1, "ayah_from": 1, "ayah_to": 1, "edition": "quran-simple", "translation": "fa.ansarian"}`
5. **No foreign keys** exist between `Post` and `QuranAyah`, preserving total isolation. If the Quran plugin is disabled or uninstalled, the Post's markdown renders seamlessly as a standard blockquote with zero runtime errors.

---

## 3. Caveats

1. **Bismillah Handling in Raw Datasets**:
   - In Surah 1 (Al-Faatiha), Bismillah is Ayah 1 in standard Hafs numbering.
   - In Surahs 2-114 (except #9 At-Tawbah), Bismillah is a header. Some raw online datasets prefix Bismillah to Ayah 1 of every Surah (`بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ الم`).
   - The importer must provide a normalization pre-processor that strips redundant Bismillah prefixes when `surah > 1 and surah != 9` if the edition format requires clean ayah text.
2. **Offline CI Test Fixtures**:
   - The full Quran contains 6,236 Ayahs per edition. Running a full import during every automated test would slow down CI.
   - To keep tests lightning-fast (< 500ms), a minimal bundled sample dataset (`sample_quran.json`) containing Surahs 1 (7 ayahs) and 112-114 (15 ayahs) is provided and used in unit/integration tests.
3. **Database Portability**:
   - Full-text search PostgreSQL features (like `to_tsvector('arabic', text)`) are not portable to SQLite.
   - By querying `normalized_text__contains=normalized_q` on pre-normalized tokens, identical behavior and 100% test compatibility are guaranteed across SQLite and PostgreSQL.

---

## 4. Conclusion

The architectural design for R2 (Official Quran Plugin) provides:
- Clean modular placement under `backend/plugins/quran/`.
- Decoupled, multi-edition relational data schema (`QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah`).
- Robust Unicode normalizer removing all Arabic/Persian diacritics and unifying character sets for cross-database search parity.
- Dynamic, source-driven, atomic JSON importer management command (`python manage.py import_quran`) supporting local files, directories, seeds, sample test datasets, and transactional rollback on validation failure.
- Complete DRF API suite for editions, surahs, ayahs, juzs, multi-edition parallel compare, and search.
- Zero-breaking Markdown injection contract for the frontend Composer action.

---

## 5. Verification Method

To independently verify the implementation during the build phase:

1. **Django App & Model Integrity**:
   ```bash
   python backend/manage.py makemigrations plugins.quran --dry-run
   python backend/manage.py check
   ```
2. **JSON Importer & Seed Data Test**:
   ```bash
   python backend/manage.py import_quran --sample
   python backend/manage.py test plugins.quran.tests.test_importer
   ```
3. **Unicode Normalizer & Search Test**:
   ```bash
   pytest backend/plugins/quran/tests/test_normalizer.py backend/plugins/quran/tests/test_search.py -v
   ```
4. **Full Test Suite & Core Non-Regression**:
   ```bash
   pytest tests/integration/ backend/plugins/quran/tests/ -v
   ```
   Verify that all 35 pre-existing tests pass with 100% success rate alongside the new Quran plugin tests.
