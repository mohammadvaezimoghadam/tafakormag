## 2026-08-23T20:25:09Z

You are Explorer 2 (Quran Plugin & Data Importer Specialist).
Your working directory is f:\AVA\tafakor\.agents\explorer_survey_2.
You must read f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md first.

Your task is to survey and design R2 (Official Quran Plugin):
1. Investigate the repository layout for plugins: where `backend/plugins/quran` or `plugins/quran` should be located and how Django loads plugin apps.
2. Design the multi-edition Quran data models: `QuranEdition` (id, identifier, name, language, type, format, etc.), `QuranSurah` (number, name, english_name, english_name_translation, revelation_type, ayah_count, etc.), `QuranAyah` (number, number_in_surah, text, normalized_text, juz, surah, edition, audio, etc.), `QuranJuz` (number, surah_mapping/metadata).
3. Design the atomic, source-driven JSON importer management command `python manage.py import_quran`: validation, transactional atomicity, dynamic dataset handling without hardcoded count assumptions, fallback/sample data bundled or downloadable.
4. Design the search mechanism: robust text normalization (Arabic/Persian diacritics removal, alef/yeh/kaf normalization) working seamlessly on SQLite (development) and PostgreSQL, search API `/api/plugins/quran/search/?q=`, surah listing `/api/plugins/quran/surahs/`, ayah navigation `/api/plugins/quran/ayahs/`, edition selection.
5. Write your complete, detailed findings with concrete schemas, importer specs, search algorithms, API contracts into f:\AVA\tafakor\.agents\explorer_survey_2\handoff.md.
6. When done, send a message to parent reporting completion and referencing the handoff report path.
