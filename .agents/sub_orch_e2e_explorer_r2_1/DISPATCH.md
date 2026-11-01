## 2026-08-23T21:01:43Z
You are Explorer 1 (Remediation Specialist: Test Harness & Tier 1 Refactoring) for Iteration 2 of the E2E Testing Track.
Your working directory is: f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_1

MANDATORY INPUTS — READ THESE FILES FIRST:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\TEST_INFRA.md
4. f:\AVA\tafakor\.agents\sub_orch_e2e\DEAD_ENDS.md
5. f:\AVA\tafakor\.agents\sub_orch_e2e_auditor_1\handoff.md (FULL FORENSIC AUDIT EVIDENCE)
6. f:\AVA\tafakor\.agents\sub_orch_e2e_reviewer_2\handoff.md (REVIEWER 2 REPORT)
7. f:\AVA\tafakor\tests\e2e\conftest.py
8. f:\AVA\tafakor\tests\e2e\test_tier1_feature_coverage.py

Your Mission:
1. Thoroughly investigate the forensic integrity violations in `tests/e2e/test_tier1_feature_coverage.py` and `tests/e2e/conftest.py`.
2. Inspect the real implementations in:
   - `backend/apps/plugin_system/models.py`, `validator.py`, `registry.py`, `views.py`, `urls.py`
   - `backend/plugins/quran/models.py`, `services/normalizer.py`, `services/search_service.py`, `services/formatter.py`, `views.py`, `urls.py`, `management/commands/import_quran.py`
   - `backend/apps/notes/models.py`, `apps/accounts/models.py`, `apps/donations/models.py`
3. Design a concrete, step-by-step remediation strategy for `test_tier1_feature_coverage.py`:
   - Replace all in-test mock dictionaries (`state = {...}`, `topic_plugins = {...}`, `ref_record = {...}`), local dummy functions (`check_topic_permission`), and self-contained classes (`ReferenceManifestValidator`, `reference_normalize_quran_text`) with authentic imports and DRF `APIClient` requests.
   - Replace all fake assertions (`cleaned = True`, `self.assertTrue(True)`, list length checks on string literals) with genuine assertions on actual database rows and API responses.
   - Fix `tests/e2e/conftest.py` to override `clean_db` for SQLite execution so `pytest tests/e2e/` runs cleanly without `flush` constraint errors.
4. Output your analysis and exact remediation plan in `f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_1\handoff.md` and call send_message to report. DO NOT implement changes yourself.
