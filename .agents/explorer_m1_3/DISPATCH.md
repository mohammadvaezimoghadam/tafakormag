## 2026-08-23T20:29:08Z
You are Explorer 3 for Milestone 1 (Generic Plugin System Core).
Working directory: f:\AVA\tafakor\.agents\explorer_m1_3

You MUST read:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m1\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_survey_1\handoff.md
5. Existing test infrastructure in `pytest.ini`, `tests/conftest.py`, `backend/apps/notes/tests.py`, `backend/apps/accounts/tests.py`, `backend/apps/donations/tests/`.

Your task:
1. Investigate the test infrastructure, pytest runner, database flush mechanisms, and test fixtures in Tafakor.
2. Design a comprehensive test suite for `backend/apps/plugin_system/tests/`:
   - `test_models.py`: Unit tests for `Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference` (creation, unique constraints, cascades, indexing, str representations).
   - `test_validator.py`: Unit tests for `ManifestValidator` (valid manifest v1, missing required fields, invalid identifier regex, invalid capabilities, invalid scopes, malformed settings schema).
   - `test_registry.py`: Unit tests for `PluginRegistry` (discovery of installed plugins, registration, lifecycle hooks, error handling on malformed plugin module).
   - `test_api.py`: Comprehensive DRF API tests for all `/api/plugins/` endpoints (marketplace list, plugin details, user install/uninstall/toggle, topic install/uninstall/toggle, permission enforcement for non-authenticated vs authenticated vs non-topic-admin).
   - `test_isolation.py`: Zero-breaking-change verification (empty `INSTALLED_TAFAKOR_PLUGINS = []`, non-regression checks).
3. Specify verification commands to ensure all 35+ existing core tests in `apps/accounts`, `apps/notes`, `apps/donations`, and `tests/integration/` continue to pass without any breaking changes.
4. Output your detailed findings and test plan to `f:\AVA\tafakor\.agents\explorer_m1_3\handoff.md`.
5. Send a completion message to the parent with a summary and reference to handoff.md.
