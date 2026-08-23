# Scope: E2E Testing Track

## Architecture & Test Strategy
The Opaque-Box E2E Testing Track provides rigorous, requirement-driven, opaque-box automated verification for the entire Tafakor Generic Plugin System and official Quran Plugin.

### Principles:
1. **Opaque-Box**: All tests interact only via public REST APIs, standard Django management commands, CLI scripts, and standard component contracts. No reliance on internal non-public private helpers or mock shortcuts.
2. **Progressive Testability**: Test runner provides clean separation across Tiers 1-4.
3. **Deterministic Isolation**: Tests run in an isolated test environment (or test DB transactions with clean flush/rollback) to prevent any persistent pollution of production data.

## Feature Inventory Coverage Matrix
| # | Feature | Tier 1 (Coverage >=5) | Tier 2 (Boundary >=5) | Tier 3 (Pairwise) | Tier 4 (Workloads) |
|---|---|:---:|:---:|:---:|:---:|
| 1 | Core Plugin Models | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 2 | Manifest Validator | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 3 | Dynamic Plugin Registry | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 4 | Settings Isolation | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 5 | Plugin Management APIs | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 6 | Multi-Edition Quran Models | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 7 | Unicode Normalizer Engine | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 8 | Atomic JSON Importer | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 9 | Cross-DB Search Engine | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 10 | Quran Navigation APIs | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 11 | Frontend Plugin Core | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 12 | Dynamic Lazy-Loading | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 13 | Marketplace UI | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 14 | Quran Mini-App Views | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 15 | Composer Action Integration | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 16 | Opaque-Box E2E Test Suite | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 17 | Core Non-Regression | 5 test cases | 5 test cases | Pairwise | Workload E2E |
| 18 | Adversarial Coverage Hardening | 5 test cases | 5 test cases | Pairwise | Workload E2E |

**Total Test Targets**:
- Tier 1: 18 * 5 = 90 test cases
- Tier 2: 18 * 5 = 90 test cases
- Tier 3: 18 pairwise interaction test cases
- Tier 4: 10 real-world end-to-end user workflow scenarios
- **Total Test Cases**: >= 208 test cases

## Sub-Milestones
| # | Name | Scope | Output Files | Status |
|---|---|---|---|---|
| M4.1 | Test Infra & Fixture Harness | Base opaque test harness, fixtures, mock dataset fixtures, API helpers | `tests/e2e/conftest.py`, `tests/e2e/test_runner.py` | PLANNED |
| M4.2 | Tier 1: Feature Coverage Suite | 90+ test cases covering all 18 features in isolation | `tests/e2e/test_tier1_feature_coverage.py` | PLANNED |
| M4.3 | Tier 2: Boundary & Corner Suite | 90+ test cases covering edge cases, unicode diacritics, empty/invalid payloads | `tests/e2e/test_tier2_boundary_cases.py` | PLANNED |
| M4.4 | Tier 3 & Tier 4 Suites | Pairwise integration & complete end-to-end user journeys | `tests/e2e/test_tier3_pairwise_combinations.py`, `tests/e2e/test_tier4_real_world_workloads.py` | PLANNED |
| M4.5 | Test Ready & Verification Publication | Publish TEST_INFRA.md and TEST_READY.md | `TEST_INFRA.md`, `TEST_READY.md` | PLANNED |
