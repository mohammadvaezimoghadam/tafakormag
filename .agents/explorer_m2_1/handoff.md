# Handoff Report: Milestone 2 — Official Quran Plugin (Backend Models, Manifest & Setup)

**Agent**: Explorer 1 (`explorer_m2_1`)  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_m2_1`  
**Target Milestone**: Milestone 2 — Official Quran Plugin (`backend/plugins/quran`)  
**Parent Agent ID**: `fb7c5ab6-89b2-41dd-921c-8284ddf8ac02`  
**Date**: 2026-08-24T00:15:30Z  

---

## 1. Observation

### 1.1 Existing Architecture & File System Findings
1. **Django App Loading & `sys.path`**:
   - In `backend/note_platform/settings.py` (lines 10–14):
     ```python
     BASE_DIR = Path(__file__).resolve().parent.parent
     sys.path.insert(0, str(BASE_DIR.parent))
     sys.path.insert(0, str(BASE_DIR))
     ```
     `backend/` and its parent directory are on `sys.path`. Placing the Quran plugin under `backend/plugins/quran/` allows referencing it as `'plugins.quran'` or `'plugins.quran.apps.QuranConfig'`.
   - In `backend/note_platform/settings.py` (lines 48–55):
     ```python
     INSTALLED_TAFAKOR_PLUGINS = [
         # Empty during M1
     ]
     for _plugin_app in INSTALLED_TAFAKOR_PLUGINS:
         if _plugin_app not in INSTALLED_APPS:
             INSTALLED_APPS.append(_plugin_app)
     ```
     Adding `'plugins.quran'` to `INSTALLED_TAFAKOR_PLUGINS` seamlessly registers the app into Django's `INSTALLED_APPS`. If `INSTALLED_TAFAKOR_PLUGINS` is cleared (`[]`), the core platform starts without any errors.

2. **Core Plugin System & Manifest Validation (`backend/apps/plugin_system/`)**:
   - `ManifestValidator.validate()` in `backend/apps/plugin_system/validator.py` (lines 37–136) strictly enforces:
     - `manifest_version`: Integer strictly equal to `1` (`isinstance(manifest_version, int)` and not `bool`).
     - `identifier`: Regex `^[a-z0-9_-]+$` (e.g. `'quran'`).
     - `name`: Non-empty string (e.g. `'Official Quran Plugin'`).
     - `version`: Semver regex `^\d+\.\d+\.\d+(-[a-zA-Z0-9_.]+)?$` (e.g. `'1.0.0'`).
     - `capabilities`: Subset of `{'composer_action', 'mini_app', 'search_provider', 'topic_integration', 'bot_action', 'feed_card'}`.
     - `scopes`: Subset of `{'read:content', 'write:composer', 'manage:topic', 'read:quran', 'write:bot'}`.
     - `settings_schema`: Valid JSON Schema Draft 7 dict.
     - `default_config`: Valid JSON conforming to `settings_schema`.
   - `PluginRegistry.autodiscover()` in `backend/apps/plugin_system/registry.py` (lines 26–79):
     - Iterates through `settings.INSTALLED_TAFAKOR_PLUGINS`.
     - Reads `manifest.json` located at `<app_path>/manifest.json`.
     - Finds any `BasePlugin` subclass in `<app_path>.plugin` or `<app_path>`.
     - Instantiates the plugin class with the validated `PluginManifest`.
     - Calls `plugin.ready()` and adds the instance to `_plugins` and `_manifests`.
     - Calls `sync_to_db()` to update/create records in the `tafakor_plugins` table.

3. **Loose Coupling & Zero Foreign Keys to Core Models**:
   - `PostPluginReference` in `backend/apps/plugin_system/models.py` (lines 142–174) connects `notes.Post` to `Plugin` via `resource_type` and `external_id` (e.g., `resource_type='ayah'`, `external_id='1:1'`).
   - Neither `notes.Post` nor `notes.Topic` has foreign keys pointing to `QuranAyah` or `QuranSurah`.
   - Disabling or uninstalling the Quran plugin leaves core posts completely functional, rendering Markdown quotes natively.

4. **URL Routing**:
   - In `backend/note_platform/urls.py` (line 29):
     `path('api/plugins/', include('apps.plugin_system.urls'))`
   - In `backend/apps/plugin_system/urls.py` (lines 29–33):
     `path('<str:identifier>/', PluginDetailView.as_view(), name='plugin-detail')`
     `path('<str:identifier>/install/', PluginUserInstallView.as_view(), ...)`
   - To route `/api/plugins/quran/...` without ambiguity, `path('api/plugins/quran/', include('plugins.quran.urls'))` must be included in `backend/note_platform/urls.py` **before** `path('api/plugins/', include('apps.plugin_system.urls'))`.

5. **Test Suite Baseline**:
   - Ran `python backend/manage.py test apps.plugin_system.tests apps.accounts apps.notes apps.donations`:
   - **Result**: 181 tests passed in 39s (111 plugin_system tests, 70 core platform tests). 0 failures, 0 errors, 0 regressions.

---

## 2. Logic Chain & Blueprint

### 2.1 Directory Structure to Create
The Quran plugin will be established in `backend/plugins/quran/`:
```
backend/plugins/
├── __init__.py
└── quran/
    ├── __init__.py
    ├── apps.py                  # QuranConfig(AppConfig)
    ├── plugin.py                # QuranPlugin(BasePlugin)
    ├── manifest.json            # Validated manifest (version 1)
    ├── models.py                # QuranEdition, QuranSurah, QuranJuz, QuranAyah
    ├── serializers.py           # DRF Serializers
    ├── views.py                 # DRF Views & ViewSets
    ├── urls.py                  # Subroutes (/editions/, /surahs/, /ayahs/, /juzs/, /search/, etc.)
    ├── services/
    │   ├── __init__.py
    │   ├── normalizer.py        # Arabic/Persian Unicode normalizer
    │   ├── search_service.py    # Cross-DB search service
    │   └── formatter.py         # Markdown reference formatter
    ├── management/
    │   ├── __init__.py
    │   └── commands/
    │       ├── __init__.py
    │       └── import_quran.py  # Atomic JSON importer command
    ├── data/
    │   ├── surahs.json          # 114 Surahs complete metadata
    │   ├── juzs.json            # 30 Juzs boundary definitions & mappings
    │   ├── editions.json        # Default editions registry metadata
    │   └── sample_quran.json    # Lightweight CI test fixture (Surahs 1, 112, 113, 114)
    ├── migrations/
    │   ├── __init__.py
    │   └── 0001_initial.py
    └── tests/
        ├── __init__.py
        ├── test_manifest.py
        ├── test_models.py
        ├── test_normalizer.py
        ├── test_importer.py
        ├── test_search.py
        └── test_api.py
```

---

### 2.2 Manifest Specification (`backend/plugins/quran/manifest.json`)

The manifest must strictly comply with `apps.plugin_system.validator.ManifestValidator`:

```json
{
  "manifest_version": 1,
  "identifier": "quran",
  "name": "Official Quran Plugin",
  "version": "1.0.0",
  "description": "Multi-edition Quran reader, search engine, and composer reference tool",
  "author": "Tafakor Core Team",
  "icon": "BookOpen",
  "is_core": true,
  "capabilities": [
    "composer_action",
    "mini_app",
    "search_provider"
  ],
  "scopes": [
    "read:content",
    "read:quran"
  ],
  "settings_schema": {
    "type": "object",
    "properties": {
      "default_edition": {
        "type": "string",
        "default": "quran-simple",
        "description": "Default Arabic text edition identifier"
      },
      "default_translation": {
        "type": "string",
        "default": "fa.ansarian",
        "description": "Default translation edition identifier"
      },
      "show_bismillah": {
        "type": "boolean",
        "default": true,
        "description": "Whether to display Bismillah before Surahs"
      }
    },
    "additionalProperties": true
  },
  "default_config": {
    "default_edition": "quran-simple",
    "default_translation": "fa.ansarian",
    "show_bismillah": true
  }
}
```

---

### 2.3 AppConfig & BasePlugin Implementation

#### `backend/plugins/quran/apps.py`
```python
from django.apps import AppConfig


class QuranConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.quran'
    verbose_name = 'Official Quran Plugin'

    def ready(self):
        # Startup hooks or signal registrations can be added here
        pass
```

#### `backend/plugins/quran/plugin.py`
```python
from apps.plugin_system.base import BasePlugin


class QuranPlugin(BasePlugin):
    """
    Official Quran Plugin class.
    Discovered and loaded automatically by apps.plugin_system.registry.PluginRegistry.
    """
    pass
```

#### `backend/plugins/quran/__init__.py`
```python
default_app_config = 'plugins.quran.apps.QuranConfig'
```

---

### 2.4 Data Models (`backend/plugins/quran/models.py`)

The multi-edition data architecture decouples Surah & Juz static canonical metadata from dynamic editions (Arabic text, Persian translations, English translations, audio streams).

```python
from django.db import models


class QuranEdition(models.Model):
    """
    Represents a specific Quran edition, translation, transliteration, or audio recitation.
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
        db_table = 'quran_editions'
        ordering = ['language', 'type', 'name']
        verbose_name = 'Quran Edition'
        verbose_name_plural = 'Quran Editions'

    def __str__(self):
        return f"{self.name} ({self.identifier})"


class QuranSurah(models.Model):
    """
    Represents the canonical 114 Surahs (chapters) of the Holy Quran.
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
        db_table = 'quran_surahs'
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
    name = models.CharField(max_length=100, blank=True, default='', help_text="e.g. 'جزء ۱', 'جزء ۳۰ (عمّ)'")
    start_surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='juz_starts')
    start_ayah = models.IntegerField(help_text="Ayah number in start surah")
    end_surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='juz_ends')
    end_ayah = models.IntegerField(help_text="Ayah number in end surah")
    surah_mapping = models.JSONField(
        default=list,
        blank=True,
        help_text="List of surah segments: [{'surah': 1, 'ayah_from': 1, 'ayah_to': 7}, ...]"
    )

    class Meta:
        db_table = 'quran_juzs'
        ordering = ['number']
        verbose_name = 'Quran Juz'
        verbose_name_plural = 'Quran Juzs'

    def __str__(self):
        return f"Juz {self.number} ({self.name or self.number})"


class QuranAyah(models.Model):
    """
    Represents an individual Ayah (verse) for a specific Edition.
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
        db_table = 'quran_ayahs'
        ordering = ['surah', 'number_in_surah']
        constraints = [
            models.UniqueConstraint(
                fields=['edition', 'number'],
                name='unique_edition_global_number'
            ),
            models.UniqueConstraint(
                fields=['edition', 'surah', 'number_in_surah'],
                name='unique_edition_surah_ayah'
            )
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
        return f"{self.edition_id} | {self.surah_id}:{self.number_in_surah}"
```

---

### 2.5 Bundled Datasets Specifications (`backend/plugins/quran/data/`)

#### 1. `backend/plugins/quran/data/surahs.json`
Complete metadata for all 114 Surahs:
- Schema per entry:
  ```json
  {
    "number": 1,
    "name": "الفاتحة",
    "english_name": "Al-Faatiha",
    "english_name_translation": "The Opening",
    "revelation_type": "Meccan",
    "ayah_count": 7,
    "order_of_revelation": 5,
    "page_start": 1,
    "page_end": 1,
    "juz_start": 1,
    "bismillah_pre": true
  }
  ```
- Important boundary cases:
  - Surah 1 (`Al-Faatiha`): 7 ayahs, Meccan, pages 1..1, `bismillah_pre: true`.
  - Surah 2 (`Al-Baqarah`): 286 ayahs, Medinan, pages 2..49, `bismillah_pre: true`.
  - Surah 9 (`At-Tawbah`): 129 ayahs, Medinan, pages 187..207, `bismillah_pre: false` (no Bismillah at start).
  - Surah 114 (`An-Naas`): 6 ayahs, Meccan, pages 604..604, `bismillah_pre: true`.

#### 2. `backend/plugins/quran/data/juzs.json`
Complete boundary data and surah mappings for all 30 Juzs:
- Schema per entry:
  ```json
  {
    "number": 1,
    "name": "جزء ۱",
    "start_surah": 1,
    "start_ayah": 1,
    "end_surah": 2,
    "end_ayah": 141,
    "surah_mapping": [
      {"surah": 1, "ayah_from": 1, "ayah_to": 7},
      {"surah": 2, "ayah_from": 1, "ayah_to": 141}
    ]
  }
  ```
- Important boundary cases:
  - Juz 1: Surah 1:1 to Surah 2:141.
  - Juz 2: Surah 2:142 to Surah 2:252.
  - Juz 3: Surah 2:253 to Surah 3:92.
  - ...
  - Juz 29: Surah 67:1 (`Al-Mulk`) to Surah 77:50 (`Al-Mursalaat`).
  - Juz 30: Surah 78:1 (`An-Naba`) to Surah 114:6 (`An-Naas`).

#### 3. `backend/plugins/quran/data/editions.json`
Pre-registered official edition specifications:
```json
[
  {
    "identifier": "quran-simple",
    "name": "متن قرآن کریم (ساده)",
    "english_name": "Simple Quran Text",
    "language": "ar",
    "type": "quran",
    "format": "text",
    "direction": "rtl",
    "author": "Tanzil Project",
    "is_default": true,
    "total_ayahs": 6236,
    "metadata": {
      "source": "https://tanzil.net",
      "license": "Creative Commons Attribution 3.0"
    }
  },
  {
    "identifier": "fa.ansarian",
    "name": "ترجمه انصاریان",
    "english_name": "Ansarian Translation",
    "language": "fa",
    "type": "translation",
    "format": "text",
    "direction": "rtl",
    "author": "حسین انصاریان",
    "is_default": true,
    "total_ayahs": 6236,
    "metadata": {
      "source": "https://erfan.ir",
      "translator": "Hossein Ansarian"
    }
  },
  {
    "identifier": "en.sahih",
    "name": "Sahih International",
    "english_name": "Sahih International",
    "language": "en",
    "type": "translation",
    "format": "text",
    "direction": "ltr",
    "author": "Saheeh International",
    "is_default": true,
    "total_ayahs": 6236,
    "metadata": {
      "source": "https://tanzil.net",
      "translator": "Emily Assami, Mary Kennedy, Amatullah Bantley"
    }
  }
]
```

#### 4. `backend/plugins/quran/data/sample_quran.json`
Lightweight CI/CD test fixture containing:
- Edition metadata for `quran-simple`, `fa.ansarian`, `en.sahih`.
- Complete Ayah datasets for Surahs 1 (7 ayahs), 112 (4 ayahs), 113 (5 ayahs), and 114 (6 ayahs) across all 3 editions (22 ayahs × 3 editions = 66 ayahs).
- Enables instantaneous test runs (`< 500ms`) with `--sample` flag for fast unit and integration tests.

---

### 2.6 Settings & URL Wiring

#### 1. `backend/note_platform/settings.py` Modification
Update line 48:
```python
INSTALLED_TAFAKOR_PLUGINS = [
    'plugins.quran',
]
```
Because lines 53–55 dynamically merge `INSTALLED_TAFAKOR_PLUGINS` into `INSTALLED_APPS`:
```python
for _plugin_app in INSTALLED_TAFAKOR_PLUGINS:
    if _plugin_app not in INSTALLED_APPS:
        INSTALLED_APPS.append(_plugin_app)
```
`'plugins.quran'` will be automatically registered when Django initializes.

#### 2. `backend/note_platform/urls.py` Modification
Add `path('api/plugins/quran/', include('plugins.quran.urls'))` before `path('api/plugins/', ...)`:
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/notes/', include('apps.notes.urls')),
    path('api/bot/', include('apps.notes.bot_urls')),
    path('api/v1/donations/', include('apps.donations.urls')),
    path('api/donations/', include('apps.donations.urls')),
    path('api/plugins/quran/', include('plugins.quran.urls')),
    path('api/plugins/', include('apps.plugin_system.urls')),
    
    # Static & media file serving
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
```

---

## 3. Caveats

1. **URL Ambiguity & Order**:
   - `apps.plugin_system.urls` contains `path('<str:identifier>/', PluginDetailView.as_view(), ...)` which can capture `'quran'`.
   - By routing `path('api/plugins/quran/', include('plugins.quran.urls'))` **first**, all plugin sub-endpoints (`/api/plugins/quran/surahs/`, `ayahs/`, `editions/`, `juzs/`, `search/`, `compare/`, `format-reference/`) resolve to `plugins.quran.urls`.
   - Requests directly to `/api/plugins/quran/` (marketplace detail) or `/api/plugins/quran/install/` fall through cleanly to `apps.plugin_system.urls` because `plugins.quran.urls` has no empty string (`''`) root match.

2. **Bismillah in Surah 9 (At-Tawbah)**:
   - In Surah 9, `bismillah_pre = False`. The UI and formatter must not prepend Bismillah when rendering or quoting Surah 9.

3. **Fast CI Test Isolation**:
   - The full Quran dataset contains 6,236 Ayahs per edition.
   - Unit tests must utilize `sample_quran.json` via `--sample` or factory helpers rather than importing the entire 6,236 ayahs in every test setup, keeping execution under a fraction of a second.

4. **Normalized Text Field**:
   - `normalized_text` must be stored alongside `text` on each `QuranAyah` record to allow high-speed substring and token matching across both SQLite and PostgreSQL without DB-specific extensions.

---

## 4. Conclusion

All models, schemas, and configuration contracts for the Quran Plugin backend have been fully designed, verified against the existing generic plugin system (`apps.plugin_system`), and documented.

The Worker can now implement:
1. `backend/plugins/quran/manifest.json` and `backend/plugins/quran/apps.py` + `plugin.py`.
2. `backend/plugins/quran/models.py` (`QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah`).
3. `backend/plugins/quran/data/` (`surahs.json`, `juzs.json`, `editions.json`, `sample_quran.json`).
4. Settings & URL wiring in `backend/note_platform/settings.py` and `backend/note_platform/urls.py`.
5. Database migrations (`python manage.py makemigrations plugins.quran`).

---

## 5. Verification Method

Once implemented by the Worker, verify independently using:

1. **Django System Check & Manifest Validation**:
   ```powershell
   python backend/manage.py check
   python backend/manage.py test plugins.quran.tests.test_manifest
   ```

2. **Model Migrations Creation & Dry Run**:
   ```powershell
   python backend/manage.py makemigrations plugins.quran
   python backend/manage.py migrate --check
   ```

3. **Model Unit Tests**:
   ```powershell
   python backend/manage.py test plugins.quran.tests.test_models
   ```

4. **Non-Regression & Full Unified Test Suite**:
   ```powershell
   python backend/manage.py test apps.plugin_system.tests apps.accounts apps.notes apps.donations plugins.quran.tests
   ```
   *Expected Result: 181 pre-existing tests + all new Quran plugin tests PASS (100%).*
