# Scope: Milestone 2 — Official Quran Plugin

## Architecture
The Official Quran Plugin (`backend/plugins/quran`) provides multi-edition Quranic data models, high-performance Unicode normalization, database-agnostic search, atomic JSON dataset importing, Composer Markdown formatting, and REST API navigation endpoints.

```
backend/plugins/
└── quran/
    ├── apps.py                  # QuranConfig & BasePlugin integration
    ├── manifest.json            # manifest_version: 1 specification
    ├── models.py                # QuranEdition, QuranSurah, QuranJuz, QuranAyah
    ├── serializers.py           # DRF Serializers
    ├── views.py                 # DRF ViewSets & Endpoints
    ├── urls.py                  # Routes /api/plugins/quran/
    ├── services/
    │   ├── normalizer.py        # Arabic/Persian Unicode diacritics & letter standardization
    │   ├── search_service.py    # Cross-DB substring & token search engine
    │   └── formatter.py         # Markdown quote builder for Composer
    ├── management/commands/
    │   └── import_quran.py      # Atomic transactional dataset importer
    ├── data/
    │   ├── surahs.json          # 114 Surahs metadata
    │   ├── juzs.json            # 30 Juzs boundary metadata
    │   ├── editions.json        # Edition registry fixtures
    │   └── sample_quran.json    # Minimal test fixtures (Surahs 1, 112-114)
    ├── migrations/              # Django migrations
    └── tests/
        ├── test_models.py
        ├── test_normalizer.py
        ├── test_importer.py
        ├── test_search.py
        └── test_api.py
```

## Feature Inventory
| # | Feature | Description | Status |
|---|---|---|---|
| 1 | Plugin Manifest & AppConfig | `manifest_version: 1`, capabilities, `INSTALLED_TAFAKOR_PLUGINS` integration | DONE |
| 2 | Multi-Edition Models | `QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah` | DONE |
| 3 | Unicode Normalizer Engine | Comprehensive diacritics stripping and letter unification | DONE |
| 4 | Search Engine Service | Cross-DB search on `normalized_text` with highlighting | DONE |
| 5 | Markdown Formatter Service | Reference formatter for Composer integration | DONE |
| 6 | Atomic JSON Importer | `import_quran` management command with `--seed`, `--sample`, `--file`, `--dir`, `--force`, `--batch-size` | DONE |
| 7 | Bundled Seed & Sample Datasets | `surahs.json` (114), `juzs.json` (30), `editions.json`, `sample_quran.json` | DONE |
| 8 | REST Navigation & Search APIs | `/api/plugins/quran/` (`editions/`, `surahs/`, `ayahs/`, `juzs/`, `search/`, `compare/`, `format-reference/`) | DONE |
| 9 | Comprehensive Plugin Test Suite | Unit and integration tests covering all Quran components (118 tests) | DONE |
| 10 | Non-Regression Verification | 100% pass rate on pre-existing core + M1 plugin system tests (299/299 unified tests) | DONE |

## Interface Contracts

### 1. Plugin Manifest
```json
{
  "manifest_version": 1,
  "identifier": "quran",
  "name": "Official Quran Plugin",
  "version": "1.0.0",
  "description": "Multi-edition Quran reader, search engine, and composer reference tool",
  "author": "Tafakor Core Team",
  "capabilities": ["composer_action", "mini_app", "search_provider"],
  "scopes": ["read:content"],
  "settings_schema": {
    "type": "object",
    "properties": {
      "default_edition": {"type": "string", "default": "quran-simple"},
      "default_translation": {"type": "string", "default": "fa.ansarian"}
    }
  },
  "default_config": {
    "default_edition": "quran-simple",
    "default_translation": "fa.ansarian"
  }
}
```

### 2. Formatter Service Contract
`format_quran_markdown_reference(surah, ayah_from, ayah_to, arabic_ayahs, translation_ayahs=None, translation_edition_name="") -> str`
Output format:
```markdown
> ﴿بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ﴾
> *به نام خداوند بخشنده مهربان*
> — **سوره الفاتحة (۱:۱)**
```

### 3. REST API Contract
- `GET /api/plugins/quran/editions/` -> List editions
- `GET /api/plugins/quran/editions/<identifier>/` -> Edition details
- `GET /api/plugins/quran/surahs/` -> List 114 Surahs
- `GET /api/plugins/quran/surahs/<int:number>/` -> Surah details
- `GET /api/plugins/quran/surahs/<int:number>/ayahs/?edition=&with_translation=&page=&page_size=&from_ayah=&to_ayah=` -> Ayahs with optional paired translation
- `GET /api/plugins/quran/ayahs/<int:number>/` -> Global ayah index
- `GET /api/plugins/quran/ayahs/<int:surah>/<int:ayah>/` -> Surah/Ayah coordinates
- `GET /api/plugins/quran/juzs/` -> List 30 Juzs
- `GET /api/plugins/quran/juzs/<int:number>/` -> Juz details
- `GET /api/plugins/quran/juzs/<int:number>/ayahs/?edition=&page=&page_size=` -> Ayahs in Juz
- `GET /api/plugins/quran/search/?q=&edition=&language=&surah=&juz=&page=&page_size=` -> Search results with `highlighted_text`
- `GET /api/plugins/quran/compare/?surah=&ayah=&editions=ed1,ed2` -> Compare across editions
- `POST /api/plugins/quran/format-reference/` -> Format Markdown reference

## Code Layout Ownership
- `backend/plugins/quran/` (Worker owns all files inside this directory)
- `backend/note_platform/settings.py` (Include `'plugins.quran'` in `INSTALLED_TAFAKOR_PLUGINS`)
- `backend/note_platform/urls.py` (Route `path('api/plugins/quran/', include('plugins.quran.urls'))`)
