# BRIEFING — 2026-08-24T00:37:30+03:30

## Mission
Implement Milestone 2: Official Quran Plugin (`plugins.quran`) including Models, Manifest, Normalizer, Search Service, Markdown Formatter, Bundled Data, JSON Importer Command, REST APIs, and comprehensive test suite with 100% pass rate.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: f:\AVA\tafakor\.agents\worker_m2_2
- Original parent: fb7c5ab6-89b2-41dd-921c-8284ddf8ac02
- Milestone: Milestone 2: Official Quran Plugin

## 🔒 Key Constraints
- Exclusive write ownership over `backend/plugins/quran/`
- Register `'plugins.quran'` in `INSTALLED_TAFAKOR_PLUGINS` in `backend/note_platform/settings.py`
- Mount `path('api/plugins/quran/', include('plugins.quran.urls'))` before `api/plugins/` in `backend/note_platform/urls.py`
- Integrity mandate: No dummy implementations, no hardcoded test shortcuts, genuine logic and state
- Full test pass across `plugins.quran.tests` and core tests (`apps.plugin_system.tests`, `apps.accounts`, `apps.notes`, `apps.donations`)

## Current Parent
- Conversation ID: fb7c5ab6-89b2-41dd-921c-8284ddf8ac02
- Updated: 2026-08-24T00:37:30+03:30

## Task Summary
- **What to build**: Full official Quran plugin for Tafakor note platform
- **Success criteria**: Genuine Quran models, migration, normalizer, search engine with highlight, formatter, datasets, import command, REST views/serializers/urls, comprehensive tests passing.
- **Interface contracts**: `f:\AVA\tafakor\.agents\sub_orch_m2\SCOPE.md`
- **Code layout**: `PROJECT.md`

## Key Decisions Made
- Used `SimpleRouter` for `plugins/quran/urls.py` so root `/api/plugins/quran/` cleanly falls through to `apps.plugin_system` detail view without routing collision.
- Stripped Bismillah prefix on Ayah 1 for Surahs 2-114 (except #9) during Arabic edition imports.
- Built diacritic-preserving highlighting via character-class regex expansion.
- Added comprehensive surah_mapping to all 30 Juz definitions in `juzs.json`.

## Change Tracker
- **Files modified**:
  - `backend/note_platform/settings.py`: added `'plugins.quran'` to `INSTALLED_TAFAKOR_PLUGINS`
  - `backend/note_platform/urls.py`: mounted `api/plugins/quran/` before `api/plugins/`
  - `backend/plugins/quran/manifest.json`: manifest_version 1, scopes, capabilities, settings schema
  - `backend/plugins/quran/apps.py`: `QuranConfig`
  - `backend/plugins/quran/plugin.py`: `QuranPlugin`
  - `backend/plugins/quran/models.py`: `QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah`
  - `backend/plugins/quran/services/normalizer.py`: Unicode normalization & diacritics stripping
  - `backend/plugins/quran/services/search_service.py`: Search engine with diacritic-preserving highlighting
  - `backend/plugins/quran/services/formatter.py`: Composer Markdown reference generator & Persian digits
  - `backend/plugins/quran/data/surahs.json`, `juzs.json`, `editions.json`, `sample_quran.json`
  - `backend/plugins/quran/management/commands/import_quran.py`: Atomic source-driven importer
  - `backend/plugins/quran/serializers.py`: DRF serializers
  - `backend/plugins/quran/views.py`: DRF ViewSets and endpoints
  - `backend/plugins/quran/urls.py`: Subroutes
  - `backend/plugins/quran/tests/`: 7 test files (`test_manifest.py`, `test_models.py`, `test_normalizer.py`, `test_search.py`, `test_formatter.py`, `test_importer.py`, `test_api.py`)
- **Build status**: PASS (230/230 tests passing)
- **Pending issues**: None

## Quality Status
- **Build/test result**: PASS (49 Quran plugin tests + 181 core/plugin_system tests = 230 tests passed)
- **Lint status**: Clean
- **Tests added/modified**: 7 comprehensive test modules in `plugins.quran.tests`

## Loaded Skills
- None

## Artifact Index
- `DISPATCH.md` — assignment dispatch
- `BRIEFING.md` — working memory
- `progress.md` — progress tracking
- `handoff.md` — completion report
