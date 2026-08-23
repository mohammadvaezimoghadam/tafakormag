## 2026-08-24T00:35:43+03:30

You are Worker 3 (Tier 3 & Tier 4 Harmonization Specialist) for Iteration 2 of the E2E Testing Track.
Your working directory is: f:\AVA\tafakor\.agents\sub_orch_e2e_worker_tier3_tier4

MANDATORY INPUTS — READ THESE FILES FIRST:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\TEST_INFRA.md
4. f:\AVA\tafakor\.agents\sub_orch_e2e\DEAD_ENDS.md
5. f:\AVA\tafakor\.agents\sub_orch_e2e_auditor_1\handoff.md
6. f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_3\handoff.md

Write Ownership: You EXCLUSIVELY own:
- tests/e2e/test_tier3_pairwise_combinations.py
- tests/e2e/test_tier4_real_world_workloads.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. Harmonize `tests/e2e/test_tier3_pairwise_combinations.py`:
   - Replace any standalone duplicate normalizer/formatter helpers with direct imports from `plugins.quran.services` (`normalize_quran_text`, `format_quran_markdown_reference`).
   - Ensure model field queries match exact `plugins.quran.models` definitions (`name`, `ayah_count`, etc.).
   - Rely on `tests/e2e/conftest.py` `clean_db` for isolation.
2. Harmonize `tests/e2e/test_tier4_real_world_workloads.py`:
   - Fix `test_scenario_01` manifest schema expectation to match `plugins/quran/manifest.json` (`default_edition`, `default_translation`, `show_bismillah`).
   - Fix `QuranSurah` model field names in scenario fixtures (`name`, `ayah_count`).
   - Import official services from `plugins.quran.services`.
3. Run verification tests:
   `pytest tests/e2e/test_tier3_pairwise_combinations.py tests/e2e/test_tier4_real_world_workloads.py -v`
   `python tests/e2e/test_runner.py --tier 3`
   `python tests/e2e/test_runner.py --tier 4`
4. Write your handoff report to `f:\AVA\tafakor\.agents\sub_orch_e2e_worker_tier3_tier4\handoff.md` and call send_message to report completion.
