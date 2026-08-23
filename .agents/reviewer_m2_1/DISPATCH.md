## 2026-08-23T21:07:52Z
You are Reviewer 1 for Milestone 2: Official Quran Plugin (`reviewer_m2_1`).
Your working directory is f:\AVA\tafakor\.agents\reviewer_m2_1.
Create your working directory state files (BRIEFING.md, progress.md) in your directory.

MANDATORY READING:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m2\SCOPE.md
4. f:\AVA\tafakor\.agents\worker_m2_2\handoff.md

Your focus:
1. Thoroughly review `backend/plugins/quran/models.py`, `apps.py`, `plugin.py`, `manifest.json`.
   - Verify `manifest_version: 1` and all required fields.
   - Verify models (`QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah`) have proper fields, indices, unique constraints, and zero direct foreign keys from core Post.
2. Thoroughly review `backend/plugins/quran/services/normalizer.py`, `services/search_service.py`, `services/formatter.py`.
   - Verify diacritics stripping (Harakat, Tashkeel, Dagger Alef, Stop Marks, Extended Quranic signs).
   - Verify letter standardizations (Alef, Yeh, Kaf, Waw, Teh Marbuta, ZWNJ, Tatweel, quotes).
   - Verify search parity across SQLite and PostgreSQL, token AND query logic, and authentic text highlighting with <mark> tags.
   - Verify Composer Markdown quote formatting with Persian/English numerals and citations.
3. Run the test suite:
   `python backend/manage.py test plugins.quran.tests`
4. Document your findings and provide your verdict (APPROVE or REQUEST_CHANGES) in `f:\AVA\tafakor\.agents\reviewer_m2_1\handoff.md`.
When finished, send a message to caller reporting your verdict and handoff path.
