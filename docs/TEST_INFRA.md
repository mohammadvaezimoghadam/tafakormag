# E2E Test Infra: Tafakor Generic Plugin System & Quran Plugin

## Test Philosophy
- **Opaque-Box & Requirement-Driven**: Derived strictly from user specifications and contracts in `ORIGINAL_REQUEST.md` and `PROJECT.md`. Tests interact only with public REST endpoints (`/api/plugins/*`), management commands (`python manage.py import_quran`), and standard frontend Markdown contracts.
- **Methodology**: 4-Tier verification combining Category-Partition, Boundary Value Analysis (BVA), Pairwise Combinatorial Testing, and Realistic End-to-End User Workload Scenarios.
- **Zero Regression**: Guarantees that pre-existing core platform behavior (Topics, Posts, Bot Tasks, SMS/Bale OTP, Donations) remains 100% functional with zero regressions when plugins are installed, disabled, or empty.

## Feature Inventory & Test Matrix
| # | Feature | Source (Requirement) | Tier 1 (Coverage) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Workload) |
|---|---|---|:---:|:---:|:---:|:---:|
| 1 | Core Plugin Models | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 2 | Manifest Validator | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 3 | Dynamic Plugin Registry | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 4 | Settings Isolation | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 5 | Plugin Management APIs | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 6 | Multi-Edition Quran Models | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 7 | Unicode Normalizer Engine | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 8 | Atomic JSON Importer | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 9 | Cross-DB Search Engine | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 10 | Quran Navigation APIs | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 11 | Frontend Plugin Core | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 12 | Dynamic Lazy-Loading | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 13 | Marketplace UI | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 14 | Quran Mini-App Views | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 15 | Composer Action Integration | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 16 | Opaque-Box E2E Test Suite | ORIGINAL_REQUEST §R4 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 17 | Core Non-Regression | ORIGINAL_REQUEST §R4 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 18 | Adversarial Coverage Hardening | ORIGINAL_REQUEST §R4 | ≥5 cases | ≥5 cases | ✓ | ✓ |

## Test Architecture

### 1. Directory Structure
```
tests/e2e/
├── conftest.py                             # Pytest fixtures, API client factories, sample datasets
├── test_runner.py                          # Unified CLI test runner executing all tiers
├── test_tier1_feature_coverage.py          # Tier 1: 90+ isolated feature test cases (18 features × 5)
├── test_tier2_boundary_cases.py            # Tier 2: 90+ edge cases, boundary inputs, unicode variations
├── test_tier3_pairwise_combinations.py     # Tier 3: 18+ pairwise cross-feature interaction test cases
└── test_tier4_real_world_workloads.py      # Tier 4: 10 realistic end-to-end user journeys
```

### 2. Invocation Commands
- **Run Full E2E Test Suite**:
  ```bash
  pytest tests/e2e/ -v
  ```
- **Run by Tier**:
  ```bash
  pytest tests/e2e/test_tier1_feature_coverage.py -v
  pytest tests/e2e/test_tier2_boundary_cases.py -v
  pytest tests/e2e/test_tier3_pairwise_combinations.py -v
  pytest tests/e2e/test_tier4_real_world_workloads.py -v
  ```
- **Run Unified Test Runner**:
  ```bash
  python tests/e2e/test_runner.py --all
  ```
- **Run Non-Regression Check on Core Platform**:
  ```bash
  pytest backend/apps/accounts/tests.py backend/apps/notes/tests.py backend/apps/donations/tests/ tests/integration/ -v
  ```

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|---|---|---|
| 1 | Full Marketplace Lifecycle: Discover, Install for User, Enable for Topic, Toggle Off, Uninstall | F1, F3, F5, F11, F13 | High |
| 2 | Quran Importer & Multi-Edition Ingestion: Atomic bulk import of Surahs, Juzs, Translations | F6, F7, F8, F10 | High |
| 3 | Deep Search & Multi-Edition Comparison: Normalized search for verses, comparison across Persian & English | F7, F9, F10, F14 | High |
| 4 | Topic Post Quran Reference Creation: Search verse -> Format Markdown -> Insert in Post -> Non-invasive Post reference | F1, F5, F7, F10, F15, F17 | Very High |
| 5 | Post Rendering & De-coupled Degradation: Topic post renders Markdown blockquote even if plugin disabled | F1, F4, F15, F17 | High |
| 6 | Topic Multi-Admin Plugin Permission Control: Topic admin enables Quran, non-admin denied config change | F1, F5, F17 | Medium |
| 7 | Custom Dataset Import Failure & Atomic Rollback: Corrupted dataset rolled back without partial corrupt state | F6, F8 | High |
| 8 | Dynamic Frontend Manifest Injection & Lazy-Load Simulation: Router adds plugin route dynamically without bundle bloat | F11, F12, F14 | High |
| 9 | Malformed Manifest Rejection & Error Boundary Resilience: Invalid manifest gracefully rejected without crashing registry | F2, F3, F11 | High |
| 10 | Complete Zero-Plugin Core Isolation Run: Server runs with `INSTALLED_TAFAKOR_PLUGINS = []`, 100% core endpoints healthy | F4, F17 | High |

## Coverage Thresholds
- **Tier 1 (Feature Coverage)**: ≥5 test cases per feature (18 × 5 = 90 test cases minimum)
- **Tier 2 (Boundary & Corner Cases)**: ≥5 test cases per feature (18 × 5 = 90 test cases minimum)
- **Tier 3 (Cross-Feature Combinations)**: ≥18 pairwise combinatorial test cases
- **Tier 4 (Real-World Workloads)**: ≥10 realistic end-to-end multi-step application scenarios
- **Total Minimum Target**: ≥208 automated test cases
