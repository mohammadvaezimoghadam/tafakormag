# Challenger 1 (Adversarial Verifier) Handoff Report

**Verdict**: `REQUEST_CHANGES`
**Timestamp**: 2026-08-24T00:34:30+03:30
**Target**: E2E Testing Track & Test Runner (`python tests/e2e/test_runner.py`)

---

## 1. Observation

Direct empirical observations from executing the E2E test runner, individual test tiers, and mutation testing harnesses:

### A. Test Runner Full Execution Failure (`python tests/e2e/test_runner.py --all`)
Executing `python tests/e2e/test_runner.py --all --verbose` resulted in **5 out of 6 test suites failing**:
```text
========================================================================================
                TAFAKOR MONOREPO - E2E & INTEGRATION TEST RUNNER SUMMARY                
========================================================================================
Suite / Target                         | Status       | Duration   | Exit Code 
---------------------------------------+--------------+------------+-----------
test_tier1_feature_coverage.py         | FAILED       | 115.41s    | 1         
test_tier2_boundary_cases.py           | FAILED       | 21.41s     | 1         
test_tier3_pairwise_combinations.py    | FAILED       | 23.81s     | 1         
test_tier4_real_world_workloads.py     | FAILED       | 11.16s     | 1         
apps.accounts apps.notes apps.don...   | PASSED       | 33.33s     | 0         
integration                            | FAILED       | 3.67s      | 2         
----------------------------------------------------------------------------------------
Total Suites: 6 | Passed: 1 | Failed: 5 | Skipped: 0 | Errors: 0
Total Execution Time: 108.73s | Result: SOME TESTS FAILED
========================================================================================
```

### B. Root Pytest Database Flushing & Locking Collision
When pytest is invoked across `tests/e2e/*`, it loads root `tests/conftest.py`:
- `tests/conftest.py` lines 37–47 defines `@pytest.fixture(autouse=True) def clean_db(django_db_blocker): call_command("flush", interactive=False, reset_sequences=True)`
- On local SQLite (`backend/db.sqlite3`), calling `flush` before each test case triggers post-migrate signals (`create_permissions`), resulting in:
  - `django.db.utils.IntegrityError: FOREIGN KEY constraint failed`
  - `sqlite3.OperationalError: database is locked`
- This causes cascading setup errors across `test_tier1_feature_coverage.py`, `test_tier2_boundary_cases.py`, and `test_tier4_real_world_workloads.py`.

### C. Model Schema Mismatches in Test Fixtures and Test Suites
1. **`QuranSurah` Model Field Names**:
   - `backend/plugins/quran/models.py` defines fields: `number`, `name`, `english_name`, `english_name_translation`, `revelation_type`, `ayah_count`, `bismillah_pre`.
   - In `tests/e2e/conftest.py` (lines 628–639), `tests/e2e/test_tier3_pairwise_combinations.py` (line 630), and `tests/e2e/test_tier4_real_world_workloads.py` (line 500), tests attempt to instantiate/query `QuranSurah` with non-existent fields: `name_ar`, `name_en`, `name_fa`, `total_ayahs`.
   - Error observed: `django.core.exceptions.FieldError: Invalid field name(s) for model QuranSurah: 'name_ar', 'name_en', 'name_fa', 'total_ayahs'.`

2. **`QuranJuz` Foreign Key Assignment**:
   - `backend/plugins/quran/models.py` defines `start_surah = models.ForeignKey(QuranSurah, ...)` and `end_surah = models.ForeignKey(QuranSurah, ...)`.
   - In `tests/e2e/conftest.py` line 614 in `seed_quran_db`, `QuranJuz.objects.get_or_create(..., defaults={"start_surah": jz["start_surah"]})` passes integer `1` rather than a `QuranSurah` model instance or `start_surah_id`.
   - Error observed: `ValueError: Cannot assign "1": "QuranJuz.start_surah" must be a "QuranSurah" instance.`

### D. Missing / Incorrect Settings Schema Key in Quran Manifest vs Tier 4 Test
- In `backend/plugins/quran/manifest.json`, `settings_schema.properties` defines `default_edition`, `default_translation`, and `show_bismillah`.
- In `tests/e2e/test_tier4_real_world_workloads.py` line 196 (`test_scenario_01_marketplace_full_lifecycle`), the test expects `assert quran.settings_schema["properties"]["font_size"]["default"] == 18`.
- Error observed: `KeyError: 'font_size'`.

### E. Missing Dependency in Non-Regression Integration Suite
- Running `tests/integration` via pytest fails at collection time on `tests/integration/test_bot_api.py` line 3: `import responses`.
- Error observed: `ModuleNotFoundError: No module named 'responses'` (exit code 2).

### F. Mutation Testing Results
- Mutating assertions in Tier 1 (`self.assertEqual(effective["font_size"], 20)` -> `9999`) and Tier 2 (`ref_record["external_id"]` -> `"mutated_wrong_id"`) were caught immediately (`AssertionError`), confirming that assertions are active and not tautological `assert True`.
- However, many tests in Tier 1 operate on mock in-memory dictionaries rather than the actual Django ORM models / database.

---

## 2. Logic Chain

1. **Premise 1 (Test Runner Executability)**: The E2E test runner (`python tests/e2e/test_runner.py --all`) is required to cleanly execute all 4 E2E tiers and core non-regression suites with a 100% success rate.
2. **Premise 2 (Database & Schema Integrity)**: Test fixtures and test cases must align exactly with the real Django model schemas (`QuranSurah`, `QuranJuz`) and plugin manifest definitions.
3. **Observation Reference**:
   - `python tests/e2e/test_runner.py --all` fails with exit code 1 (5 out of 6 suites fail).
   - Pytest execution against SQLite fails due to `tests/conftest.py`'s `clean_db` fixture calling `flush` on every test.
   - `QuranSurah` queries in `conftest.py`, `test_tier3`, and `test_tier4` crash with `FieldError` due to non-existent fields (`name_ar`, `name_en`, `name_fa`, `total_ayahs`).
   - `QuranJuz` creation crashes with `ValueError` on integer assignment to ForeignKey.
   - `test_scenario_01` crashes with `KeyError: 'font_size'`.
   - `test_bot_api.py` crashes with `ModuleNotFoundError: No module named 'responses'`.
4. **Conclusion from Logic**: Because the test runner cannot run to completion and the test suite contains blocking schema and fixture errors, the current work product fails verification.

---

## 3. Caveats

- Tier 1 and Tier 2 test suites execute successfully when run in isolation under Django's test runner (`python backend/manage.py test`) because Django's test runner isolates tests using memory SQLite databases rather than invoking the root `clean_db` `call_command("flush")` fixture.
- Core Django app tests (`backend/manage.py test apps.accounts apps.notes apps.donations`) pass with 100% success rate (70 tests pass in 33.33s).

---

## 4. Conclusion

**Verdict: `REQUEST_CHANGES`**

The following concrete fixes are required before E2E testing can be approved:

1. **Fix `tests/conftest.py` & Test Runner isolation**:
   - Modify `clean_db` fixture in `tests/conftest.py` to skip `flush` when running on SQLite or when `e2e_db_cleaner` is active, or configure `test_runner.py` to run E2E suites with isolated test database settings to prevent SQLite file locks and foreign key errors.
2. **Fix `QuranSurah` & `QuranJuz` field references in E2E tests**:
   - Update `tests/e2e/conftest.py`, `test_tier3_pairwise_combinations.py`, and `test_tier4_real_world_workloads.py` to use authentic `QuranSurah` fields (`name`, `english_name`, `english_name_translation`, `ayah_count`).
   - In `tests/e2e/conftest.py` `seed_quran_db`, pass `start_surah=surahs[jz["start_surah"]]` and `end_surah=surahs[jz["end_surah"]]` (or `start_surah_id=...`).
3. **Harmonize Quran Plugin Manifest & Tier 4 settings assertion**:
   - Align `backend/plugins/quran/manifest.json` `settings_schema` and `test_tier4_real_world_workloads.py` `test_scenario_01_marketplace_full_lifecycle` so that `settings_schema` properties match.
4. **Fix Integration Non-Regression Suite**:
   - Either mock the HTTP requests in `tests/integration/test_bot_api.py` without requiring the uninstalled `responses` package or ensure dependencies are aligned.

---

## 5. Verification Method

To independently reproduce all findings and verify fixes:

```bash
# 1. Run the unified test runner across all tiers (must pass with exit code 0)
python tests/e2e/test_runner.py --all

# 2. Run Tier 3 & Tier 4 specifically with pytest
python -m pytest tests/e2e/test_tier3_pairwise_combinations.py -v
python -m pytest tests/e2e/test_tier4_real_world_workloads.py -v

# 3. Run Core Non-Regression integration suite
python -m pytest tests/integration/ -v
```
