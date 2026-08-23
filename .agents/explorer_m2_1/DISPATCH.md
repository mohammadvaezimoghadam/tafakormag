## 2026-08-24T00:13:29Z

You are Explorer 1 for Milestone 2 (Official Quran Plugin).
Your working directory is f:\AVA\tafakor\.agents\explorer_m2_1.
Create your working directory state files (BRIEFING.md, progress.md) in your directory.

MANDATORY READING:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m2\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_survey_2\handoff.md
5. f:\AVA\tafakor\.agents\sub_orch_m1\handoff.md

Your focus:
1. Django App setup for `backend/plugins/quran/apps.py` (QuranConfig inheriting AppConfig or registering with plugin registry) and `backend/plugins/quran/manifest.json` (validating against `apps.plugin_system.validator.ManifestValidator`).
2. Data models in `backend/plugins/quran/models.py`:
   - `QuranEdition` (identifier pk, name, english_name, language, type, format, direction, author, is_default, total_ayahs, metadata, timestamps)
   - `QuranSurah` (number pk 1-114, name, english_name, english_name_translation, revelation_type, ayah_count, order_of_revelation, page_start, page_end, juz_start, bismillah_pre)
   - `QuranJuz` (number pk 1-30, name, start_surah, start_ayah, end_surah, end_ayah, surah_mapping JSONField)
   - `QuranAyah` (id BigAutoField pk, edition FK, surah FK, number global 1-6236, number_in_surah, juz, manzil, page, ruku, hizb_quarter, sajda JSONField, text TextField, normalized_text TextField indexed, audio_url, metadata JSONField).
   - Check unique constraints, compound indexes, and foreign key relations.
   - Verify zero direct foreign keys from core Post to QuranAyah.
3. Bundled datasets in `backend/plugins/quran/data/`:
   - `surahs.json` (complete metadata for 114 Surahs)
   - `juzs.json` (complete boundary data for 30 Juzs)
   - `editions.json` (default editions: simple Arabic, Ansarian Persian translation, Sahih International English translation)
   - `sample_quran.json` (test fixture containing Surahs 1, 112, 113, 114 for quick test execution)
4. Settings and URL wiring in `backend/note_platform/settings.py` and `backend/note_platform/urls.py`.

Investigate the existing codebase and produce a detailed handoff report in `f:\AVA\tafakor\.agents\explorer_m2_1\handoff.md` with concrete code snippets and model definitions for the Worker.
When finished, send a message to caller (parent) reporting completion.
