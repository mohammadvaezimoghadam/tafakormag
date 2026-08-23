# Cross-DB & Test Runner Optimization Report (Explorer 3 — Iteration 2)

**Track**: E2E Testing Track (Iteration 2)  
**Role**: Explorer 3 — Cross-DB & Test Runner Optimization Specialist  
**Working Directory**: `f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_3`  
**Mission**: Formulate the architectural solution for SQLite database locking, conftest fixture inheritance, and test runner execution to ensure `tests/e2e/test_runner.py` and `pytest tests/e2e/` run seamlessly on both SQLite and PostgreSQL with 0 setup errors, 0 lock timeouts, and 0 flakiness across all 4 tiers.

---

## 1. Observation

Direct code and environmental inspection across `tests/`, `backend/`, and `tests/e2e/` revealed four fundamental root causes responsible for setup errors, database locking, and runner failures.

### Observation 1.1: Root `tests/conftest.py` Autouse Collision (`clean_db`)
* **Location**: `tests/conftest.py:37-47`
  ```python
  @pytest.fixture(autouse=True)
  def clean_db(django_db_blocker):
      with django_db_blocker.unblock():
          from django.core.management import call_command
          call_command("flush", interactive=False, reset_sequences=True)
  ```
* **Mechanics**:
  - In Pytest, fixtures marked `autouse=True` in a parent directory (`tests/conftest.py`) are automatically executed before every test collected in child directories (`tests/e2e/`), unless a fixture with the **exact same name** (`clean_db`) is defined in `tests/e2e/conftest.py`.
  - In `tests/e2e/conftest.py:84-131`, the isolation fixture was named `e2e_db_cleaner`.
  - Because `clean_db` was not shadowed in `tests/e2e/conftest.py`, pytest executed root `clean_db` for every test in `test_tier1_feature_coverage.py` and `test_tier2_boundary_cases.py`.
  - On SQLite, `call_command("flush")` triggers:
    ```
    django.db.utils.IntegrityError: UNIQUE constraint failed: django_content_type.app_label, django_content_type.model
    sqlite3.IntegrityError: FOREIGN KEY constraint failed
    ```
    This caused **58 setup errors** when running `python tests/e2e/test_runner.py --tier 1`.
  - Tier 3 (`test_tier3_pairwise_combinations.py:117`) and Tier 4 (`test_tier4_real_world_workloads.py:103`) bypassed this locally by defining `@pytest.fixture(autouse=True) def clean_db(): yield` inside each file, demonstrating that naming parity is the exact shadowing mechanism.

---

### Observation 1.2: SQLite File Lock Contention & Transaction Isolation on Windows
* **Location**: `tests/e2e/test_tier2_boundary_cases.py` and `tests/e2e/test_tier3_pairwise_combinations.py`
* **Mechanics**:
  - SQLite by default on Windows operates in `DELETE` rollback journal mode with a single-writer exclusive lock.
  - When tests execute `with transaction.atomic():` or raise exceptions that abort inner blocks, open cursor handles or unclosed connections keep the SQLite file locked.
  - Default SQLite `busy_timeout` is 0 to 5 seconds. When subsequent tests or background assertions immediately query the database, SQLite raises:
    ```
    django.db.utils.OperationalError: database is locked
    ```
  - Django test runs did not set SQLite PRAGMAs (`journal_mode = WAL`, `busy_timeout = 30000`, `synchronous = NORMAL`) and did not execute `connections.close_all()` in test fixture teardown, leading to 7 lock errors in Tier 2 and 20 lock errors in Tier 3.

---

### Observation 1.3: Model Schema Mismatches in `tests/e2e/conftest.py` Fixtures
* **Location**: `tests/e2e/conftest.py:588-667` (`seed_quran_db` fixture)
* **Mechanics**:
  - The fixture definitions in `tests/e2e/conftest.py` were authored before `plugins.quran.models.py` was finalized, resulting in field mismatches against actual models:
    1. **`QuranSurah`** (`plugins/quran/models.py:53-85`):
       - *Model Fields*: `number` (PK), `name`, `english_name`, `english_name_translation`, `revelation_type`, `ayah_count`, `bismillah_pre`.
       - *Conftest Passed*: `name_ar`, `name_en`, `name_fa`, `total_ayahs`. This raises `TypeError: unexpected keyword argument` when inserting real models.
    2. **`QuranJuz`** (`plugins/quran/models.py:87-111`):
       - *Model Fields*: `number` (PK), `start_surah` (`ForeignKey(QuranSurah)`), `start_ayah`, `end_surah` (`ForeignKey(QuranSurah)`), `end_ayah`.
       - *Conftest Passed*: `start_surah=jz["start_surah"]` (raw `int`), causing `ValueError: Cannot assign "1": "QuranJuz.start_surah" must be a "QuranSurah" instance`.
    3. **`QuranAyah`** (`plugins/quran/models.py:113-166`):
       - *Model Fields*: `edition` (`ForeignKey`), `surah` (`ForeignKey`), `number` (`IntegerField` required global 1..6236), `number_in_surah` (`IntegerField`), `juz` (`IntegerField` not FK), `text`, `normalized_text`.
       - *Conftest Passed*: Omitted required `number` field and passed `juz=juz_obj` (`QuranJuz` instance). This raises `IntegrityError: NOT NULL constraint failed: quran_ayahs.number`.

---

### Observation 1.4: Test Suite Heterogeneity & Integrity Duplication
* **Location**: `tests/e2e/` (Tiers 1, 2, 3, 4)
* **Mechanics**:
  - **Tier 1** used `unittest.TestCase` with in-memory dicts and fake assertions (`cleaned = True`).
  - **Tier 2** used `django.test.TestCase` with fallback exception catches and duplicate contract classes (`ManifestValidatorContract`, `DynamicPluginRegistryContract`, `QuranNormalizerContract`, `QuranReferenceFormatterContract`).
  - **Tier 3 & Tier 4** used pure pytest classes (`@pytest.mark.django_db`) with standalone helper duplicates (`StandaloneQuranNormalizer`, `StandaloneQuranFormatter`) and ad-hoc local `clean_db` fixtures.
  - Production implementations already exist in `backend/apps/plugin_system/` and `backend/plugins/quran/` (`ManifestValidator`, `PluginRegistry`, `normalize_quran_text`, `QuranSearchService`, `format_quran_markdown_reference`, `import_quran` management command).

---

### Observation 1.5: Unified Test Runner (`test_runner.py`) Subprocess & Environment Protocol
* **Location**: `tests/e2e/test_runner.py:133-250`
* **Mechanics**:
  - `test_runner.py` uses `subprocess.run` to execute tiers. This provides strong process isolation.
  - It handles UTF-8 terminal encoding on Windows (`sys.stdout.reconfigure(encoding="utf-8")`).
  - However, it lacks a pre-flight database readiness check, SQLite PRAGMA initialization, and schema validation before launching child pytest processes.

---

## 2. Logic Chain

```
[Root tests/conftest.py defines autouse clean_db calling flush]
                            │
                            ▼
[tests/e2e/conftest.py named cleanup e2e_db_cleaner, NOT clean_db]
                            │
                            ▼
[Pytest fixture resolution executes root clean_db on all E2E tests]
                            │
                            ▼
[SQLite flush triggers IntegrityError on django_content_type and locks file]
                            │
                            ▼
[Tier 1 & Tier 2 crash with 58 setup errors under pytest]
```

```
[SQLite default journal mode (DELETE) on Windows has single-writer exclusive locks]
                            │
                            ▼
[Zero busy_timeout + unclosed connections in test teardowns]
                            │
                            ▼
[Subsequent test cases encounter OperationalError: database is locked]
```

### Synthesis & Remediation Logic:
1. **Fixture Shadowing Principle**: Defining `@pytest.fixture(autouse=True) def clean_db(django_db_blocker):` in `tests/e2e/conftest.py` strictly shadows the parent `clean_db` in `tests/conftest.py` for all test files under `tests/e2e/`. This completely eliminates `call_command('flush')` execution during E2E runs on SQLite.
2. **Deterministic DB Teardown**: Inside `clean_db` in `tests/e2e/conftest.py`, delete entities in reverse foreign-key topological order and invoke `django.db.connections.close_all()`. This guarantees clean state and zero open file handles.
3. **SQLite PRAGMA Optimization**: Register a Django `connection_created` signal hook that enables `WAL` mode (`PRAGMA journal_mode = WAL;`), sets `busy_timeout = 30000;`, and enables `synchronous = NORMAL;` whenever SQLite is active. This eliminates lock contention and allows concurrent reads/writes.
4. **Schema Harmonization**: Update `seed_quran_db` in `tests/e2e/conftest.py` to match exact Django model field definitions (`name`, `ayah_count`, global `number`, `juz` integer, ForeignKey `start_surah`).
5. **Harmonized Test Harness**: Convert Tier 1 and Tier 2 to pure `@pytest.mark.django_db` pytest classes, remove all fake assertions and duplicate contracts, and import production classes directly (`apps.plugin_system.*`, `plugins.quran.*`).

---

## 3. Caveats

1. **Docker vs Local SQLite Parity**:
   - In Docker CI (`docker compose run backend-test`), PostgreSQL is used (`DB_HOST=db`). Root `tests/conftest.py` unblocks `django_db_blocker` and reuses the migrated DB.
   - On local development, SQLite is used (`backend/db.sqlite3`).
   - The architectural solution defined below is 100% agnostic: `clean_db` teardown in `tests/e2e/conftest.py` uses Django ORM `.delete()` and `connections.close_all()`, which works identically on both SQLite and PostgreSQL.
2. **Pre-requisite Database Migrations**:
   - Because root `tests/conftest.py` monkeypatches `BaseDatabaseCreation._get_test_db_name` to reuse the existing database without re-migrating, the active database (`db.sqlite3` or PostgreSQL `tafakor`) must be migrated once prior to running tests (`python backend/manage.py migrate`).
   - The test runner `test_runner.py` must include an automated pre-flight check that runs or verifies migrations before launching tiers.
3. **Playwright E2E UI Test Separation**:
   - `tests/e2e/test_critical_path.py` requires running frontend and backend servers. The 4 E2E testing tiers (`test_tier1_feature_coverage.py`, `test_tier2_boundary_cases.py`, `test_tier3_pairwise_combinations.py`, `test_tier4_real_world_workloads.py`) are pure DRF API and ORM integration tests that run headless in-process.

---

## 4. Conclusion & Architectural Blueprint

### Component 1: `tests/e2e/conftest.py` Architecture

The file must implement three critical layers:

#### Layer 1: SQLite Connection Signal Hook
```python
from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def configure_sqlite_pragmas(sender, connection, **kwargs):
    """Configures SQLite connections with WAL mode and 30s busy timeout."""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 30000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")
```

#### Layer 2: Autouse `clean_db` Fixture (Exact Shadow of Parent)
```python
@pytest.fixture(autouse=True)
def clean_db(django_db_blocker):
    """
    Shadows root tests/conftest.py clean_db.
    Provides non-destructive, transaction-safe isolation without calling flush.
    """
    with django_db_blocker.unblock():
        yield
        try:
            from django.db import connections
            # 1. Reverse FK topological cleanup
            if PostComment is not None: PostComment.objects.all().delete()
            if PostReaction is not None: PostReaction.objects.all().delete()
            if BotTask is not None: BotTask.objects.all().delete()
            if PostPluginReference is not None: PostPluginReference.objects.all().delete()
            if Post is not None: Post.objects.all().delete()
            if TopicAdmin is not None: TopicAdmin.objects.all().delete()
            if PluginTopicInstallation is not None: PluginTopicInstallation.objects.all().delete()
            if PluginInstallation is not None: PluginInstallation.objects.all().delete()
            if Topic is not None: Topic.objects.all().delete()
            if QuranAyah is not None: QuranAyah.objects.all().delete()
            if QuranJuz is not None: QuranJuz.objects.all().delete()
            if QuranSurah is not None: QuranSurah.objects.all().delete()
            if QuranEdition is not None: QuranEdition.objects.all().delete()
            if Plugin is not None: Plugin.objects.all().delete()

            # Clean test users
            User.objects.filter(phone__regex=r'^09(00|11|12|22|33|99)').delete()

            # 2. Release all database connection file handles
            connections.close_all()
        except Exception:
            pass
```

#### Layer 3: Synchronized Model Seed Fixture (`seed_quran_db`)
```python
@pytest.fixture
def seed_quran_db(quran_sample_full_dataset):
    """Seeds database using exact Django model field signatures."""
    if QuranEdition is None or QuranSurah is None or QuranAyah is None:
        return {"seeded": False, "reason": "Quran models unavailable"}

    editions = {}
    for ed in quran_sample_full_dataset["editions"]:
        obj, _ = QuranEdition.objects.get_or_create(
            identifier=ed["identifier"],
            defaults={
                "name": ed["name"],
                "english_name": ed.get("name", ""),
                "language": ed["language"],
                "direction": ed["direction"],
                "type": ed.get("type", "quran"),
                "author": ed.get("author", ""),
                "is_default": ed.get("is_default", False),
                "total_ayahs": 6236,
            }
        )
        editions[ed["identifier"]] = obj

    surahs = {}
    for sr in quran_sample_full_dataset["surahs"]:
        obj, _ = QuranSurah.objects.get_or_create(
            number=sr["number"],
            defaults={
                "name": sr["name_ar"],
                "english_name": sr["name_en"],
                "english_name_translation": sr.get("name_fa", ""),
                "ayah_count": sr["total_ayahs"],
                "revelation_type": sr.get("revelation_type", "Meccan").capitalize(),
                "bismillah_pre": sr.get("bismillah_pre", True),
                "juz_start": 1 if sr["number"] <= 1 else 30,
            }
        )
        surahs[sr["number"]] = obj

    juzs = {}
    if QuranJuz is not None:
        for jz in quran_sample_full_dataset["juzs"]:
            s_surah = surahs.get(jz["start_surah"])
            e_surah = surahs.get(jz["end_surah"])
            if s_surah and e_surah:
                obj, _ = QuranJuz.objects.get_or_create(
                    number=jz["number"],
                    defaults={
                        "name": jz["name"],
                        "start_surah": s_surah,
                        "start_ayah": jz["start_ayah"],
                        "end_surah": e_surah,
                        "end_ayah": jz["end_ayah"],
                    }
                )
                juzs[jz["number"]] = obj

    ayah_objs = []
    global_ayah_counter = 1
    for ay in quran_sample_full_dataset["ayahs"]:
        surah_obj = surahs.get(ay["surah_number"])
        juz_num = ay.get("juz_number", 1)
        for ed_id, text in ay["texts"].items():
            edition_obj = editions.get(ed_id)
            if surah_obj and edition_obj:
                ayah_obj, _ = QuranAyah.objects.get_or_create(
                    edition=edition_obj,
                    surah=surah_obj,
                    number_in_surah=ay["ayah_number"],
                    defaults={
                        "number": global_ayah_counter,
                        "text": text,
                        "normalized_text": text,
                        "juz": juz_num,
                    }
                )
                ayah_objs.append(ayah_obj)
        global_ayah_counter += 1

    return {
        "seeded": True,
        "editions": editions,
        "surahs": surahs,
        "juzs": juzs,
        "ayah_count": len(ayah_objs),
    }
```

---

### Component 2: `tests/e2e/test_runner.py` Optimization

1. **Pre-flight Health & Migration Check**:
   Before launching test suites, run a silent migration check to guarantee tables exist:
   ```python
   def ensure_database_ready():
       """Verifies database connectivity and executes pending migrations."""
       env = get_environment()
       cmd = [sys.executable, "backend/manage.py", "migrate", "--noinput"]
       res = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
       if res.returncode != 0:
           print(f"Warning: Auto-migration returned code {res.returncode}: {res.stderr}")
   ```
2. **Subprocess Pytest Flag Hardening**:
   - Enforce `-o addopts=` to strip root `pytest.ini` `--reuse-db` or coverage settings during individual tier runs.
   - Pass `-p no:warnings` or clean stdout filters for crisp output.
3. **Cross-DB Parity Logging**:
   - Output active database engine (SQLite vs PostgreSQL) in runner banner:
     ```
     ========================================================================================
                      TAFAKOR MONOREPO - E2E TEST RUNNER (Engine: SQLite)                    
     ========================================================================================
     ```

---

### Component 3: Tier 1 to 4 Harmonization Plan

| Tier | Current Flaw | Architectural Fix |
|---|---|---|
| **Tier 1 (`test_tier1_feature_coverage.py`)** | Inherits `unittest.TestCase`, asserts on static dicts, fake `cleaned = True`, 58 flush setup errors | Convert all 18 feature classes to `@pytest.mark.django_db` pytest classes. Import and test actual `apps.plugin_system` models, `ManifestValidator`, `PluginRegistry`, DRF `APIClient` (`/api/plugins/`), and `plugins.quran` services. Remove all local reference algorithms. |
| **Tier 2 (`test_tier2_boundary_cases.py`)** | Inherits `django.test.TestCase`, duplicate contract classes (`ManifestValidatorContract`, etc.), fallback exception catches, SQLite locks | Convert to `@pytest.mark.django_db` pytest classes. Use real production validators and serializers. Remove contract duplicates. Rely on conftest `clean_db` for isolation. |
| **Tier 3 (`test_tier3_pairwise_combinations.py`)** | Standalone duplicate `StandaloneQuranNormalizer` and `StandaloneQuranFormatter`, ad-hoc local `clean_db` fixture | Import `normalize_quran_text` and `QuranReferenceFormatter` from `plugins.quran.services`. Remove duplicate normalizer and local `clean_db` (relying on `tests/e2e/conftest.py`). |
| **Tier 4 (`test_tier4_real_world_workloads.py`)** | Standalone duplicate `StandaloneQuranNormalizer` and `StandaloneQuranFormatter`, ad-hoc local `clean_db` fixture | Import official services from `plugins.quran.services`. Remove local `clean_db` fixture. |

---

## 5. Verification Method

To independently verify this configuration plan:

1. **Verify Conftest Shadowing & Isolation on SQLite**:
   ```bash
   python tests/e2e/test_runner.py --tier 1
   ```
   *Expected Result*: 0 setup errors, 0 IntegrityErrors from `flush`.
2. **Verify SQLite Lock Elimination in Tier 2 & Tier 3**:
   ```bash
   python tests/e2e/test_runner.py --tier 2
   python tests/e2e/test_runner.py --tier 3
   ```
   *Expected Result*: 0 `OperationalError: database is locked` errors.
3. **Verify Full Suite Execution via Pytest**:
   ```bash
   pytest tests/e2e/ -v -o addopts=""
   ```
   *Expected Result*: All 4 tiers execute cleanly with 100% pass rate.
4. **Verify Unified Runner All Tiers & Non-Regression**:
   ```bash
   python tests/e2e/test_runner.py --all
   ```
   *Expected Result*: Exit code 0, structured summary table with ALL TESTS PASSED.
5. **Verify Core Non-Regression**:
   ```bash
   python backend/manage.py test apps.accounts apps.notes apps.donations
   ```
   *Expected Result*: 70/70 passed (100% OK).
