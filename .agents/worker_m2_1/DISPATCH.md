## 2026-08-24T00:16:29Z

You are the Worker for Milestone 2: Official Quran Plugin (`worker_m2_1`).
Your working directory is f:\AVA\tafakor\.agents\worker_m2_1.
Create your working directory state files (BRIEFING.md, progress.md) in your directory.

MANDATORY READING:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m2\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_m2_1\handoff.md (Models, Manifest, Settings, Data schema)
5. f:\AVA\tafakor\.agents\explorer_m2_2\handoff.md (Unicode Normalizer, Search Engine, Markdown Formatter)
6. f:\AVA\tafakor\.agents\explorer_m2_3\handoff.md (JSON Importer, REST Views, Serializers, URLs, Test Suite)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE WRITE OWNERSHIP:
- You exclusively own all files inside `backend/plugins/quran/`
- You edit `backend/note_platform/settings.py` (add `'plugins.quran'` to `INSTALLED_TAFAKOR_PLUGINS`)
- You edit `backend/note_platform/urls.py` (add `path('api/plugins/quran/', include('plugins.quran.urls'))` before `api/plugins/`)

TASKS TO COMPLETE:
1. Create `backend/plugins/quran/` package with:
   - `__init__.py`
   - `apps.py` (`QuranConfig`)
   - `plugin.py` (`QuranPlugin(BasePlugin)`)
   - `manifest.json` (`manifest_version: 1`, identifier: "quran", capabilities: ["composer_action", "mini_app", "search_provider"], scopes: ["read:content", "read:quran"], settings_schema and default_config)
2. Implement Models in `backend/plugins/quran/models.py`:
   - `QuranEdition` (identifier pk, name, english_name, language, type, format, direction, author, is_default, total_ayahs, metadata, created_at, updated_at)
   - `QuranSurah` (number pk 1-114, name, english_name, english_name_translation, revelation_type, ayah_count, order_of_revelation, page_start, page_end, juz_start, bismillah_pre)
   - `QuranJuz` (number pk 1-30, name, start_surah FK, start_ayah, end_surah FK, end_ayah, surah_mapping JSONField)
   - `QuranAyah` (id BigAutoField pk, edition FK, surah FK, number global 1-6236, number_in_surah, juz, manzil, page, ruku, hizb_quarter, sajda JSONField, text TextField, normalized_text TextField db_index=True, audio_url, metadata JSONField).
   - Add constraints: `UniqueConstraint(fields=['edition', 'number'])`, `UniqueConstraint(fields=['edition', 'surah', 'number_in_surah'])`.
   - Add compound indexes: `['edition', 'surah', 'number_in_surah']`, `['edition', 'juz']`, `['edition', 'page']`, `['surah', 'number_in_surah']`, `['edition', 'normalized_text']`.
3. Implement Services in `backend/plugins/quran/services/`:
   - `services/normalizer.py`: `normalize_quran_text()`, `strip_quranic_diacritics()` (Tashkeel, Harakat, Dagger Alef \u0670, Stop Marks \u06D6-\u06DC, \u06DF-\u06E8, \u06EA-\u06ED, \u08D4-\u08FF, letter standardizations for Alef, Yeh, Kaf, Waw, Teh Marbuta, ZWNJ, Tatweel, quotes/brackets).
   - `services/search_service.py`: `search_quran()` / `search_quran_ayahs()`, `highlight_authentic_text()` / `build_highlight_regex_for_token()` (multi-word token AND queries, exact phrase matching, cross-DB parity on SQLite and PostgreSQL, diacritic-preserving highlighting).
   - `services/formatter.py`: `format_quran_markdown_reference()`, `to_persian_digits()`, `format_ayah_model_reference()`.
4. Create Bundled Datasets in `backend/plugins/quran/data/`:
   - `surahs.json` (complete metadata for 114 Surahs)
   - `juzs.json` (complete boundary data for 30 Juzs)
   - `editions.json` (default editions: quran-simple, fa.ansarian, en.sahih)
   - `sample_quran.json` (lightweight CI test fixture with Surahs 1, 112, 113, 114 across quran-simple, fa.ansarian, en.sahih)
5. Implement Management Command `backend/plugins/quran/management/commands/import_quran.py`:
   - Arguments: `--seed`, `--sample`, `--file`, `--dir`, `--force`, `--batch-size`.
   - Dynamic schema detection (Al-Quran Cloud nested format, flat ayahs list, surah dictionary map, multi-edition bundle).
   - Transactional atomicity via `transaction.atomic()`.
   - Bismillah prefix stripping on Ayah 1 for Surahs 2-114 (except #9) when type == 'quran'.
   - Bulk inserts with `QuranAyah.objects.bulk_create(batch_size=batch_size)`.
6. Implement Serializers, Views, and URLs in `backend/plugins/quran/`:
   - `serializers.py`
   - `views.py` (`QuranEditionViewSet`, `QuranSurahViewSet`, `QuranJuzViewSet`, `QuranAyahDetailByGlobalView`, `QuranAyahDetailBySurahView`, `QuranSearchView`, `QuranCompareView`, `QuranFormatReferenceView`)
   - `urls.py`
7. Wire Settings and Main URLs:
   - In `backend/note_platform/settings.py`, ensure `'plugins.quran'` is in `INSTALLED_TAFAKOR_PLUGINS`.
   - In `backend/note_platform/urls.py`, include `path('api/plugins/quran/', include('plugins.quran.urls'))`.
8. Create Django Migrations:
   - Run `python manage.py makemigrations plugins.quran`
   - Apply migrations `python manage.py migrate`
9. Create Full Test Suite in `backend/plugins/quran/tests/`:
   - `test_manifest.py` (manifest validator verification)
   - `test_models.py` (model creation, str, constraints, cascading delete)
   - `test_normalizer.py` (diacritics, letters, dagger alef, invisible chars, idempotence)
   - `test_search.py` (token search, multi-word AND, exact phrase, filtering, highlighting)
   - `test_formatter.py` (single ayah, ayah range, translation, Persian digits)
   - `test_importer.py` (sample import, file import, error handling & transactional rollback, bismillah stripping)
   - `test_api.py` (all endpoints: editions, surahs, ayahs, juzs, search, compare, format-reference)
10. Execute and Verify All Tests:
   - Run `python manage.py test plugins.quran.tests`
   - Run all core non-regression tests: `python manage.py test apps.plugin_system.tests apps.accounts apps.notes apps.donations`
   - Verify 100% tests pass with 0 errors, 0 failures.

Write your final completion report in `f:\AVA\tafakor\.agents\worker_m2_1\handoff.md` and call `send_message` back to caller when done.
