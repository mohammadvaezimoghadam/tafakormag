## 2026-08-23T21:05:42Z
You are Worker 2 (Tier 2 Boundary Cases Refactoring Specialist) for Iteration 2 of the E2E Testing Track.
Your working directory is: f:\AVA\tafakor\.agents\sub_orch_e2e_worker_tier2

MANDATORY INPUTS — READ THESE FILES FIRST:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\TEST_INFRA.md
4. f:\AVA\tafakor\.agents\sub_orch_e2e\DEAD_ENDS.md
5. f:\AVA\tafakor\.agents\sub_orch_e2e_auditor_1\handoff.md (FULL FORENSIC AUDIT EVIDENCE)
6. f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_2\handoff.md (TIER 2 REFACTORING BLUEPRINT)

Write Ownership: You EXCLUSIVELY own:
- tests/e2e/test_tier2_boundary_cases.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. Completely Refactor `tests/e2e/test_tier2_boundary_cases.py`:
   - Delete all 5 duplicate local contract classes (`BasePluginContract`, `ManifestValidatorContract`, `DynamicPluginRegistryContract`, `QuranNormalizerContract`, `QuranReferenceFormatterContract`).
   - Import and test actual production classes: `apps.plugin_system.validator.ManifestValidator`, `apps.plugin_system.registry.PluginRegistry`, `apps.plugin_system.models.*`, `plugins.quran.models.*`, `plugins.quran.services.normalizer.normalize_quran_text`, `plugins.quran.services.formatter.format_quran_markdown_reference`, `plugins.quran.services.search_service.search_quran`, and DRF API endpoints.
   - Refactor all 18 feature boundary test classes (>= 90 boundary test cases) testing true boundary inputs (malformed manifests, out-of-range Surah/Juz/Ayah numbers, 401/403/404 API boundaries, empty/long search queries, Unicode bombs, SQL injection safety).
   - Wrap `IntegrityError` tests in inner `transaction.atomic()` and use unique phone prefixes (`0988...`) to prevent SQLite database lock contention.
2. Run verification tests:
   `pytest tests/e2e/test_tier2_boundary_cases.py -v`
   `python tests/e2e/test_runner.py --tier 2`
3. Write your handoff report to `f:\AVA\tafakor\.agents\sub_orch_e2e_worker_tier2\handoff.md` and call send_message to report completion.
