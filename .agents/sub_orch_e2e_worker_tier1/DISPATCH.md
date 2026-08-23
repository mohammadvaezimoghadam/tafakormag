## 2026-08-24T00:35:42Z
You are Worker 1 (Test Harness & Tier 1 Refactoring Specialist) for Iteration 2 of the E2E Testing Track.
Your working directory is: f:\AVA\tafakor\.agents\sub_orch_e2e_worker_tier1

MANDATORY INPUTS — READ THESE FILES FIRST:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\TEST_INFRA.md
4. f:\AVA\tafakor\.agents\sub_orch_e2e\DEAD_ENDS.md
5. f:\AVA\tafakor\.agents\sub_orch_e2e_auditor_1\handoff.md (FULL FORENSIC AUDIT EVIDENCE)
6. f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_1\handoff.md (TIER 1 REFACTORING BLUEPRINT)
7. f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_3\handoff.md (CROSS-DB & RUNNER BLUEPRINT)

Write Ownership: You EXCLUSIVELY own:
- tests/e2e/conftest.py
- tests/e2e/test_runner.py
- tests/e2e/test_tier1_feature_coverage.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. Refactor `tests/e2e/conftest.py`:
   - Add `@pytest.fixture(autouse=True) def clean_db(): yield` to shadow the root `tests/conftest.py:clean_db` and eliminate SQLite `flush` crashes.
   - Configure SQLite PRAGMAs (`WAL`, `busy_timeout = 30000`, `synchronous = NORMAL`).
   - Fix model field names in `seed_quran_db` fixture (`QuranSurah.name`, `ayah_count`, `QuranJuz.start_surah`, `QuranAyah.number`).
   - Ensure clean database teardown and connection closing in `e2e_db_cleaner`.
2. Refactor `tests/e2e/test_runner.py`:
   - Add pre-flight migration check and pytest subprocess flag hardening (`-o addopts=`).
3. Completely Refactor `tests/e2e/test_tier1_feature_coverage.py`:
   - Delete all in-test mock dictionaries (`state = {...}`, `topic_plugins = {...}`, `campaign = {...}`, etc.), fake assertions (`cleaned = True`, `self.assertTrue(True)`), and local duplicate classes (`ReferenceManifestValidator`, `reference_normalize_quran_text`).
   - Implement all 18 feature test classes (5 genuine test cases each = 90 test cases) using real imports from `apps.plugin_system.models`, `validator`, `registry`, `views`, `plugins.quran.models`, `services.normalizer`, `services.search_service`, `services.formatter`, `management.commands.import_quran`, and core models (`User`, `Topic`, `Post`, `BotTask`, `DonationCampaign`).
   - All tests must use genuine assertions against actual DB records, DRF `APIClient` responses, and authentic services.
4. Run verification tests:
   `pytest tests/e2e/test_tier1_feature_coverage.py -v`
   `python tests/e2e/test_runner.py --tier 1`
5. Write your handoff report to `f:\AVA\tafakor\.agents\sub_orch_e2e_worker_tier1\handoff.md` and call send_message to report completion.
