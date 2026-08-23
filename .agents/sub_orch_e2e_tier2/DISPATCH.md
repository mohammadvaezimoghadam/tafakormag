## 2026-08-23T20:29:43Z
You are Test Writer 3 (Tier 2 Boundary & Corner Cases Specialist) for the E2E Testing Track of Tafakor Monorepo.
Your working directory is: f:\AVA\tafakor\.agents\sub_orch_e2e_tier2
Files you MUST read before starting:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\TEST_INFRA.md

Write Ownership: You EXCLUSIVELY own:
- tests/e2e/test_tier2_boundary_cases.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. Create `tests/e2e/test_tier2_boundary_cases.py` covering ALL 18 features from `PROJECT.md § Feature Inventory` with at least 5 boundary/corner test cases per feature (>= 90 test cases total):
   - Empty, None, and whitespace strings
   - Extreme out-of-range numbers (Surah 0, 115, Ayah 0, 9999, negative IDs, huge pagination numbers)
   - Unicode diacritics, dagger alefs, Quranic pause marks, ZWNJ, tatweel, special glyphs
   - Malformed manifests, missing required keys, invalid types, invalid versions
   - Search query boundaries (1-char, 1000-char, punctuation-only, diacritic-only)
   - Unauthenticated & unauthorized permission violations
   - Database constraint boundaries (uniqueness violations, cascades)
   - Importer error boundaries (corrupted JSON, missing files, invalid surah IDs)
2. All test cases must use genuine assertions testing boundary rejection, error codes (400, 401, 403, 404), and error handling without crashes.
3. Structure tests cleanly with descriptive docstrings (e.g. `TestTier2Feature01CorePluginModelsBoundaries`, etc.).
4. Write your completion report to `f:\AVA\tafakor\.agents\sub_orch_e2e_tier2\handoff.md` and call send_message to report completion.
