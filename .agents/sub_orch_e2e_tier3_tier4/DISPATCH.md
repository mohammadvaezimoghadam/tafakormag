## 2026-08-23T20:29:43Z
You are Test Writer 4 (Tier 3 & Tier 4 Combinations & Workloads Specialist) for the E2E Testing Track of Tafakor Monorepo.
Your working directory is: f:\AVA\tafakor\.agents\sub_orch_e2e_tier3_tier4
Files you MUST read before starting:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\TEST_INFRA.md

Write Ownership: You EXCLUSIVELY own:
- tests/e2e/test_tier3_pairwise_combinations.py
- tests/e2e/test_tier4_real_world_workloads.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. Create `tests/e2e/test_tier3_pairwise_combinations.py` with >= 18 pairwise interaction test cases covering:
   - Plugin installation + Topic post creation with plugin reference
   - Plugin disable + Post rendering (graceful degradation)
   - Quran importer + Search API instant discovery
   - Quran Unicode normalizer + Search query matching
   - Quran verse picker + Markdown formatting + Topic post publishing + Bot task generation
   - Marketplace install + Topic admin vs non-admin permissions
   - Multi-edition parallel compare API
   - Manifest validator + Dynamic registry reload
   - Dynamic route injection + Error boundary fallback
   - Empty settings fallback + Core auth & notes operations
   - Bulk Ayah import + Pagination & Surah navigation
   - Surah 9 (At-Tawbah, no bismillah) + Verse reader formatting
   - Audio stream URL resolution + Ayah pagination
   - PostPluginReference lookup + Topic post listing
   - Non-admin user topic plugin toggling rejection
   - Multi-term token search across normalized Arabic & Persian
   - Plugin uninstall + Post reference retention
   - Core donation campaign creation alongside topic plugin references
2. Create `tests/e2e/test_tier4_real_world_workloads.py` with 10 realistic end-to-end user workflows:
   - Scenario 1: Marketplace End-to-End Discovery, Installation, Topic Enablement, and Teardown
   - Scenario 2: Full Ingestion & Search Lifecycle
   - Scenario 3: Study & Comparison Workflow
   - Scenario 4: Topic Author Workflow (Search -> Format Markdown -> Publish Post -> Verify Bot Task)
   - Scenario 5: Graceful Degradation Verification
   - Scenario 6: Multi-Admin Topic Access Control Workflow
   - Scenario 7: Corrupted Data Ingestion & Transactional Rollback Recovery
   - Scenario 8: Frontend Dynamic Manifest Loading & Route Activation Flow
   - Scenario 9: Plugin Error Boundary Isolation under Component Exception
   - Scenario 10: Complete Zero-Plugin Isolation Platform Check
3. Write your completion report to `f:\AVA\tafakor\.agents\sub_orch_e2e_tier3_tier4\handoff.md` and call send_message to report completion.
