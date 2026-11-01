## 2026-08-24T00:13:29+03:30

You are Explorer 3 for Milestone 2 (Official Quran Plugin).
Your working directory is f:\AVA\tafakor\.agents\explorer_m2_3.
Create your working directory state files (BRIEFING.md, progress.md) in your directory.

MANDATORY READING:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m2\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_survey_2\handoff.md
5. f:\AVA\tafakor\.agents\sub_orch_m1\handoff.md

Your focus:
1. Dynamic, Source-Driven Atomic JSON Importer Command in `backend/plugins/quran/management/commands/import_quran.py`:
   - Arguments: `--seed`, `--sample`, `--file <path>`, `--dir <path>`, `--force`, `--batch-size <int>`.
   - Support multiple input JSON formats dynamically (Al-Quran Cloud standard structure, flat Ayah list, surah dictionary format) without hardcoded ayah count assumptions.
   - Transactional atomicity via `transaction.atomic()`: all-or-nothing rollback on validation failure.
   - Bismillah prefix handling: In Surahs 2-114 (except #9), strip prepended Bismillah if dataset prefixes it to Ayah 1.
   - Bulk insertion optimization with `bulk_create(batch_size=batch_size)`.
2. REST API Endpoints, Serializers, and Views in `backend/plugins/quran/`:
   - `serializers.py`: `QuranEditionSerializer`, `QuranSurahSerializer`, `QuranSurahDetailSerializer`, `QuranJuzSerializer`, `QuranAyahSerializer`, `QuranAyahDetailSerializer`, `QuranSearchResponseSerializer`, `QuranCompareSerializer`, `QuranFormatReferenceSerializer`.
   - `views.py`:
     - `QuranEditionViewSet` (`/api/plugins/quran/editions/`)
     - `QuranSurahViewSet` (`/api/plugins/quran/surahs/`, `/api/plugins/quran/surahs/<id>/ayahs/`)
     - `QuranAyahViewSet` (`/api/plugins/quran/ayahs/<global_number>/`, `/api/plugins/quran/ayahs/<surah>/<ayah>/`)
     - `QuranJuzViewSet` (`/api/plugins/quran/juzs/`, `/api/plugins/quran/juzs/<id>/ayahs/`)
     - `QuranSearchView` (`/api/plugins/quran/search/`)
     - `QuranCompareView` (`/api/plugins/quran/compare/`)
     - `QuranFormatReferenceView` (`/api/plugins/quran/format-reference/`)
   - `urls.py`: Clean routing registered under `path('api/plugins/quran/', include('plugins.quran.urls'))`.
3. Test Suite Design (`backend/plugins/quran/tests/`):
   - Model tests (`test_models.py`), normalizer tests (`test_normalizer.py`), search tests (`test_search.py`), importer tests (`test_importer.py`), API tests (`test_api.py`).

Investigate and produce a detailed handoff report in `f:\AVA\tafakor\.agents\explorer_m2_3\handoff.md` with complete serializers, views, URL routes, management command logic, and test plan for the Worker.
When finished, send a message to caller (parent) reporting completion.
