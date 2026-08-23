# Empirical Challenger Report: Milestone 2 — Official Quran Plugin (Services & Search)

**Agent**: Challenger 1 (`challenger_m2_1`)  
**Working Directory**: `f:\AVA\tafakor\.agents\challenger_m2_1`  
**Verdict**: **APPROVE**  
**Date**: 2026-08-24T00:42:30+03:30  
**Parent Conversation ID**: `fb7c5ab6-89b2-41dd-921c-8284ddf8ac02`  

---

## 1. Observation

1. **Target Components Under Stress Test**:
   - Unicode Normalizer: `backend/plugins/quran/services/normalizer.py`
   - Search Engine Service: `backend/plugins/quran/services/search_service.py`
   - Markdown Formatter Service: `backend/plugins/quran/services/formatter.py`
   - Data Models & Relationships: `backend/plugins/quran/models.py`

2. **Adversarial Test Suite Executed**:
   - Test suite `backend/plugins/quran/tests/test_adversarial_challenger.py` containing 28 exhaustive adversarial test methods across 3 test case classes:
     - `QuranNormalizerAdversarialTests`: 9 test cases
     - `QuranSearchEngineAdversarialTests`: 11 test cases
     - `QuranFormatterAdversarialTests`: 8 test cases
   - Combined with existing unit tests (`test_normalizer.py`, `test_search.py`, `test_formatter.py`), a total of 49 targeted service tests were executed.

3. **Empirical Execution Command & Results**:
   - **Command**:
     ```powershell
     python backend/manage.py test plugins.quran.tests.test_normalizer plugins.quran.tests.test_search plugins.quran.tests.test_formatter plugins.quran.tests.test_adversarial_challenger
     ```
   - **Result**: `Ran 49 tests in 0.237s. OK. 100% pass rate.`
   - **Full Non-Regression Suite**:
     ```powershell
     python backend/manage.py test apps.plugin_system.tests apps.accounts apps.notes apps.donations
     ```
   - **Result**: `Ran 181 tests in 40.352s. OK. 100% pass rate. 0 regressions.`

---

## 2. Logic Chain

1. **Unicode Normalization Resilience**:
   - **Dense Overlapping Diacritics**: Tests stacked 10+ diacritical and combining marks (Fatha, Damma, Kasra, Shaddah, Tanwin, Sukun, Maddah, Dagger Alef, Stop signs `\u064E\u064F\u0650\u0651\u064B\u064C\u064D\u0652\u0653\u0670\u06D6\u06E1`) on a single consonant. `strip_quranic_diacritics` and `normalize_quran_text` stripped all marks cleanly down to the bare letter `ب`.
   - **Dagger Alefs & High Hamzas**: Verified Quranic words with superscript dagger alef (`هَٰذَا` -> `هذا`, `سَمَٰوَٰتِ` -> `سموت`, `رَحْمَٰنِ` -> `رحمن`) and high hamza (`\u0674`) normalize deterministically.
   - **Hamza & Alef Orthographic Variants**: Tested all variations (`أ`, `إ`, `آ`, `ٱ` Wasla, `ٲ`, `ٳ`, `ٵ`). All unify to standard bare `ا`.
   - **Arabic Presentation Forms A & B**: Isolated, initial, medial, and final forms (`\uFE8F`, `\uFED9`, `\uFEF1`, `\uFEFB`, `\uFB8E-\uFB91`, `\uFB56`, `\uFB7A`) properly decompose via NFKD into canonical Arabic/Persian letters (`ب ک ی`, `لا ا`, `ک ک ک ک`, `پ چ`).
   - **Zero-Width & Directional Controls**: ZWNJ (`\u200c`), NBSP (`\u00a0`), and line/paragraph separators (`\u2028`, `\u2029`) cleanly convert to single spaces, while ZWJ (`\u200d`), LRM (`\u200e`), RLM (`\u200f`), BOM (`\ufeff`), LRE/RLE/PDF/LRO/RLO (`\u202a-\u202e`), and isolate controls (`\u2066-\u2069`) are stripped without leaving orphan invisible codes.
   - **Quranic Stop & Pause Signs**: Signs (`\u06D6-\u06DC`, `\u06DF-\u06E8`, `\u06EA-\u06ED`, `\u08D4-\u08FF`, Sajda `۩`, Rub-el-Hizb `۞`, Ayah end `۝`) and Tatweel/Kashida (`ـ`) are stripped.
   - **Idempotence & Performance**: Verified `normalize_quran_text(normalize_quran_text(x)) == normalize_quran_text(x)`. High-throughput benchmark normalized an 80KB repetitive Quranic text in < 0.05s.

2. **Search Engine & Highlighting Robustness**:
   - **Regex Injection Safety**: Adversarial payloads containing unescaped regex metacharacters (`(`, `[`, `]`, `*`, `+`, `?`, `\`, `^`, `$`, `.*`, `(((.*)+)+)`, `\u064E+`, `(?i)`) executed without crashing, raising `re.error`, or stalling in catastrophic backtracking (ReDoS).
   - **Authentic Text Diacritic Highlighting**: The highlighter uses dynamic character-class pattern construction with diacritic skips (`[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u08D4-\u08E1\u08E3-\u08FF\u0640]*`). Matched terms in Uthmani and Simple scripts are enclosed in `<mark>...</mark>` tags without stripping authentic Tashkeel or producing nested/malformed HTML tags.
   - **Repeated Terms in Long Verses**: Highlighting correctly tagged multiple instances of search terms across long verses (such as Ayat al-Kursi).
   - **Exact Phrase vs Token Queries**: Verified `exact=True` (or quoted queries `"..."`) strictly enforces phrase adjacency and order in `normalized_text`, while unquoted multi-word queries execute tokenized `AND` matching.
   - **Mixed Persian / Arabic Scripts**: Queries with Persian `ک`/`ی` match authentic Arabic verses with `ك`/`ي`/`ى` and vice-versa.
   - **Missing Translations & Empty Inputs**: Querying non-existent translation editions returns `None` for translation without crashing; empty or whitespace-only queries return empty result sets with `total_matches = 0`.

3. **Markdown Formatter Fidelity**:
   - **Blockquote Standard**: Single ayahs format as `> ﴿{arabic}﴾\n> *{translation}*\n> — **سوره {name} ({coord})**`.
   - **Multi-Verse Ranges**: Range citations insert Persian/ASCII verse end ornaments (`۝۱`, `۝۲`) and coordinate ranges (`۱:۱-۳`).
   - **Language Support**: `lang="fa"` produces Persian numerals and labels (`سوره الفاتحة (۱:۱-۲)`), while `lang="en"` produces ASCII numerals and English labels (`Surah Al-Faatiha (1:1-2)`).
   - **Robust Error Handling**: Handles mismatched translation array lengths, `None` translation inputs, empty verse lists, model instances, dictionary objects, and raw strings gracefully without throwing exceptions.

---

## 3. Caveats

1. **Database Search Backend**: Search uses normalized substring queries (`normalized_text__contains`) which ensures 100% identical behavior between SQLite (used in CI/unit tests) and PostgreSQL (production). Full-text index extensions (like pg_trgm or PostgreSQL tsvector) can be layered as an optional optimization in the future without modifying this interface contract.
2. **No other caveats**: All services adhere strictly to specifications and survive all adversarial inputs.

---

## 4. Conclusion

**Verdict: APPROVE**

The Unicode Normalizer (`services/normalizer.py`), Search Engine (`services/search_service.py`), and Markdown Formatter (`services/formatter.py`) are empirically verified to be sound, performant, resilient to adversarial inputs, and compliant with all project requirements.

---

## 5. Verification Method

To reproduce and verify these empirical results:

1. **Run Challenger 1 Adversarial & Service Test Suite**:
   ```powershell
   python backend/manage.py test plugins.quran.tests.test_normalizer plugins.quran.tests.test_search plugins.quran.tests.test_formatter plugins.quran.tests.test_adversarial_challenger
   ```
   *Expected: 49 tests passed (OK).*

2. **Run Full Monorepo Non-Regression Test Suite**:
   ```powershell
   python backend/manage.py test apps.plugin_system.tests apps.accounts apps.notes apps.donations
   ```
   *Expected: 181 tests passed (OK).*
