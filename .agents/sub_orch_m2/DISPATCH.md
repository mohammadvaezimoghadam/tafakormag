## 2026-08-23T20:42:35Z

Implement Milestone 2: Official Quran Plugin (`backend/plugins/quran/`).
Scope:
- Multi-edition models: `QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah` (decoupled, zero foreign keys from core Post to QuranAyah).
- Unicode Normalizer: Arabic/Persian diacritics stripping & letter standardization (`services/normalizer.py`).
- Cross-DB Search Engine: Querying over `normalized_text` with parity on SQLite and PostgreSQL (`services/search_service.py`).
- Markdown Formatter for Composer: (`services/formatter.py`).
- Management Command: `python manage.py import_quran` (atomic transactional JSON importer with dynamic dataset handling, `--seed`, `--sample`, `--file`, `--dir`, `--force`, and `--batch-size`).
- Bundled seed/sample datasets in `backend/plugins/quran/data/` (`surahs.json` [114 surahs], `juzs.json` [30 juzs], `editions.json`, `sample_quran.json`).
- REST API endpoints for `/api/plugins/quran/` (`editions/`, `surahs/`, `ayahs/`, `juzs/`, `search/`, `compare/`, `format-reference/`).
- Complete test suite in `backend/plugins/quran/tests/` covering models, normalizer, importer, search, and APIs.
- Non-regression: Verify all pre-existing tests + M1 tests continue to pass with 100% success rate.
