## 2026-08-24T00:13:30Z

You are Explorer 2 for Milestone 2 (Official Quran Plugin).
Your working directory is f:\AVA\tafakor\.agents\explorer_m2_2.
Create your working directory state files (BRIEFING.md, progress.md) in your directory.

MANDATORY READING:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m2\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_survey_2\handoff.md
5. f:\AVA\tafakor\backend\apps\notes\models.py (check existing Persian normalization)

Your focus:
1. Unicode Normalization Engine in `backend/plugins/quran/services/normalizer.py`:
   - Comprehensive stripping of Arabic/Persian diacritics (Harakat, Tashkeel, Sukun, Tanwin, Shaddah, Maddah, Dagger Alef \u0670).
   - Stripping of Quranic pause marks, stop signs (\u06D6-\u06DC, \u06DF-\u06E8, \u06EA-\u06ED), Sajda marks, Rub el Hizb.
   - Normalizing letter variations: Alef (أ, إ, آ, ٱ, ٲ, ٳ, ٵ -> ا), Yeh (ي, ى, ئ -> ی), Kaf (ك -> ک), Waw (ؤ -> و), Teh Marbuta (ة, ۀ -> ه), Tatweel (ـ -> remove).
   - Handling invisible chars: ZWNJ (\u200c -> space), ZWJ (\u200d -> remove), LRM/RLM/BOM.
   - Handling Arabic quotes/brackets (﴿, ﴾, «, », , ۞, ۩).
   - Deterministic behavior across all Arabic/Persian scripts.
2. Search Engine Service in `backend/plugins/quran/services/search_service.py`:
   - Fast, cross-database search query builder over `normalized_text`.
   - Guaranteed identical results and performance on SQLite and PostgreSQL.
   - Multi-word token `AND` queries vs exact phrase search.
   - Highlighting algorithm: produce `highlighted_text` in authentic text with `<mark>` tags without losing original diacritics.
   - Filtering by edition, language, surah, juz, and pagination.
3. Markdown Formatter Service in `backend/plugins/quran/services/formatter.py`:
   - Format standard blockquote for single Ayah and Ayah ranges with Surah reference and optional translation.
   - Support Persian and English citation labels.

Investigate and produce a detailed handoff report in `f:\AVA\tafakor\.agents\explorer_m2_2\handoff.md` with complete algorithms, regexes, and service implementations for the Worker.
When finished, send a message to caller (parent) reporting completion.
