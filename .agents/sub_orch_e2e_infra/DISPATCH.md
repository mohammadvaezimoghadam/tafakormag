## 2026-08-23T20:29:43Z
<USER_REQUEST>
You are Test Writer 1 (Test Infra & Harness Specialist) for the E2E Testing Track of Tafakor Monorepo.
Your working directory is: f:\AVA\tafakor\.agents\sub_orch_e2e_infra
Files you MUST read before starting:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\TEST_INFRA.md
4. f:\AVA\tafakor\tests\conftest.py

Write Ownership: You EXCLUSIVELY own:
- tests/e2e/conftest.py
- tests/e2e/test_runner.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. Create `tests/e2e/conftest.py`:
   - DRF APIClient and user fixtures (`api_client`, `auth_client`, `topic_admin_client`, `other_user_client`).
   - Fixtures for creating test Users, Topics, Posts.
   - Seed data helper fixtures for Quran sample data (Surahs 1, 112, 113, 114) and editions (`quran-simple`, `fa.ansarian`, `en.sahih`).
   - Sample manifest generator fixture for testing plugin validator and registry.
   - Ensure complete DB isolation and compatibility with standard pytest and Django test runner.
2. Create `tests/e2e/test_runner.py`:
   - Unified CLI runner supporting `--tier 1`, `--tier 2`, `--tier 3`, `--tier 4`, `--all`, `--non-regression`.
   - Provides clean test discovery, execution summary, and exit codes.
3. Verify the fixtures and runner syntax.
4. Write your completion report to `f:\AVA\tafakor\.agents\sub_orch_e2e_infra\handoff.md` and call send_message to report completion.
</USER_REQUEST>
