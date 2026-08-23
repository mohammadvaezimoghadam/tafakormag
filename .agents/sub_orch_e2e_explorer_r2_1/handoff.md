# Remediation Strategy & Architectural Blueprint: Test Harness & Tier 1 Refactoring

**Agent**: Explorer 1 (Remediation Specialist: Test Harness & Tier 1 Refactoring)  
**Iteration**: 2 (E2E Testing Track)  
**Date**: 2026-08-24  
**Working Directory**: `f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_1`

---

## 1. Observation

A forensic investigation of the E2E test harness and Tier 1 test suite (`tests/e2e/test_tier1_feature_coverage.py` and `tests/e2e/conftest.py`) along with the real backend implementation (`apps/plugin_system`, `plugins/quran`, `apps/notes`, `apps/accounts`, `apps/donations`) revealed the following concrete observations:

### A. Root Cause of Pytest / SQLite Harness Collisions (`tests/conftest.py` vs `tests/e2e/conftest.py`)
1. **Root `clean_db` Fixture Collision**:
   - In `tests/conftest.py` (lines 37–46):
     ```python
     @pytest.fixture(autouse=True)
     def clean_db(django_db_blocker):
         with django_db_blocker.unblock():
             from django.core.management import call_command
             call_command("flush", interactive=False, reset_sequences=True)
     ```
   - When running `pytest tests/e2e/`, pytest discovers the root `tests/conftest.py`. On SQLite, `call_command("flush")` attempts to reset tables and re-emit `post_migrate` signals, triggering:
     ```
     django.db.utils.IntegrityError: UNIQUE constraint failed: django_content_type.app_label, django_content_type.model
     sqlite3.IntegrityError: FOREIGN KEY constraint failed
     ```
   - While `test_tier3_pairwise_combinations.py:117` and `test_tier4_real_world_workloads.py:103` included local `clean_db` overrides (`@pytest.fixture(autouse=True) def clean_db(): yield`), `tests/e2e/conftest.py` defined `e2e_db_cleaner` without defining `clean_db`. This caused 58 setup errors when running Tier 1 under pytest.

### B. Forensic Violations in `tests/e2e/test_tier1_feature_coverage.py`
Across all 18 feature test classes (1594 lines), tests were executing against self-contained mock dictionaries and dummy algorithms instead of the actual platform codebase:

1. **Self-Certifying Local Duplicate Contracts**:
   - Lines 56–86: Defines local `reference_normalize_quran_text` and `QURANIC_DIACRITICS_REGEX`.
   - Lines 95–158: Defines local `ReferenceManifestValidator` and `ManifestValidationException`.
   - Lines 285–361 (Feature 02): Tests `ReferenceManifestValidator.validate` instead of `apps.plugin_system.validator.ManifestValidator`.
   - Lines 743–770 (Feature 07): Tests `reference_normalize_quran_text` instead of `plugins.quran.services.normalizer.normalize_quran_text`.
   - Lines 1533–1570 (Feature 18): Validates adversarial inputs against `ReferenceManifestValidator` and `reference_normalize_quran_text`.

2. **In-Memory Dictionary Mocks Masquerading as ORM Models & REST APIs**:
   - Lines 170–274 (Feature 01: Core Plugin Models): Asserts on `plugin_dict = {...}`, `topic_installation = {...}`, and `ref = {...}` without instantiating `Plugin`, `PluginInstallation`, `PluginTopicInstallation`, or `PostPluginReference`.
   - Lines 377–466 (Feature 03: Dynamic Plugin Registry): Initializes `self.registry = {}` and tests local dict queries and a local `SamplePlugin` class instead of `apps.plugin_system.registry.PluginRegistry`.
   - Lines 541–625 (Feature 05: Plugin Management APIs): Asserts on `sample_response = [...]`, `state = {"installed": False, ...}`, and a local dummy function `check_topic_permission` instead of executing DRF `APIClient` requests against `/api/plugins/`.
   - Lines 636–730 (Feature 06: Multi-Edition Quran Models): Asserts on local dictionaries `edition = {...}`, `surah_1 = {...}`, `juz_1 = {...}`, `ayah = {...}` instead of `QuranEdition`, `QuranSurah`, `QuranJuz`, and `QuranAyah` Django models.
   - Lines 783–875 (Feature 08: Atomic JSON Importer): Simulates atomicity using a local Python list `staged.clear()` instead of invoking `call_command('import_quran', ...)`.
   - Lines 888–960 (Feature 09: Cross-DB Search Engine): Implements a local string search `self._search` over `self.corpus` with Python `split()` and `in` instead of testing `plugins.quran.services.search_service.search_quran` or database querysets.
   - Lines 972–1031 (Feature 10: Quran Navigation APIs): Simulates API pagination and lookups using Python slice operations and dictionaries instead of calling `/api/plugins/quran/` REST endpoints.
   - Lines 1043–1408 (Features 11–15): Asserts against in-memory dictionary states for frontend core, lazy loader, marketplace UI, mini-app views, and composer actions.

3. **Fake Assertions & Trivial Constant Checks**:
   - Line 501 (`test_f04_c03`): `else: self.assertTrue(True)` fallback.
   - Line 1427 (`test_f16_c01`): Asserts `self.assertEqual(len(expected_files), 4)` on a static list of 4 strings rather than checking filesystem paths.
   - Line 1432 (`test_f16_c02`): Asserts `self.assertEqual(cli_args["--tier"], "1")` on a static dictionary rather than testing `test_runner.py`'s `argparse` parser.
   - Line 1438 (`test_f16_c03`): `cleaned = True; self.assertTrue(cleaned)` instead of executing database cleanup verification.
   - Lines 1473–1520 (Feature 17: Core Non-Regression): Asserts `self.assertEqual(len(user_data["phone"]), 11)` on `user_data = {"phone": "09123456789"}` and asserts on static dictionaries for campaigns and bot tasks rather than testing `apps.accounts.models.User`, `apps.notes.models.Topic`, `Post`, `BotTask`, and `apps.donations.models.DonationCampaign`.
   - Line 1589 (`test_f18_c05`): Asserts on local boolean `is_valid = isinstance(bad_s, int) and (1 <= bad_s <= 114)` instead of running `import_quran` on corrupt dataset files.

### C. Available Platform Implementations for Authentic Refactoring
Direct inspection verified that the actual backend code is fully implemented, verified, and ready for integration:
- `backend/apps/plugin_system/`:
  - `models.py`: `Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference`
  - `validator.py`: `ManifestValidator` with `ALLOWED_CAPABILITIES`, `ALLOWED_SCOPES`, `IDENTIFIER_REGEX`, JSON Schema validation
  - `registry.py`: `PluginRegistry`, `plugin_registry`, `BasePlugin`, `PluginManifest`
  - `views.py` & `urls.py`: Full REST API views mounted under `/api/plugins/`
- `backend/plugins/quran/`:
  - `models.py`: `QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah`
  - `services/normalizer.py`: `normalize_quran_text`, `strip_quranic_diacritics`
  - `services/search_service.py`: `search_quran`, `highlight_authentic_text`, `QuranSearchService`
  - `services/formatter.py`: `format_quran_markdown_reference`, `format_ayah_model_reference`, `QuranMarkdownFormatter`
  - `views.py` & `urls.py`: Full REST API views mounted under `/api/plugins/quran/`
  - `management/commands/import_quran.py`: Atomic importer supporting `--file`, `--dry-run`, `--force`
- Core Platform Models:
  - `apps.accounts.models.User`
  - `apps.notes.models.Topic`, `Post`, `TopicAdmin`, `PostReaction`, `PostComment`, `BotTask`
  - `apps.donations.models.DonationCampaign`

---

## 2. Logic Chain

1. **Contract Requirement**: `ORIGINAL_REQUEST.md` (Integrity Mode: `development`) and `TEST_INFRA.md` mandate that all test tiers must be opaque-box, requirement-driven, and interact directly with real Django models, DRF API clients, management commands, and backend services. Fake assertions and self-certifying mock contracts are strictly forbidden.
2. **From Observation A**: The root `clean_db` fixture in `tests/conftest.py` fails on SQLite because `flush` causes content-type constraint errors. Overriding `clean_db` with an autouse empty yield fixture in `tests/e2e/conftest.py` solves this cleanly for the entire `tests/e2e/` package, leaving table-level cleanup to `e2e_db_cleaner`.
3. **From Observation B**: All 18 feature test classes in `test_tier1_feature_coverage.py` currently test in-memory dictionaries, local dummy algorithms, and fake assertions. None of them exercise the actual platform codebase.
4. **From Observation C**: Because all production models, validators, registries, commands, and API endpoints exist and pass their unit suites (70/70 core tests pass, 111/111 plugin system tests pass), Tier 1 can be 100% refactored to import and execute genuine platform code with zero mock facades.
5. **Conclusion**: Refactoring `tests/e2e/conftest.py` and `tests/e2e/test_tier1_feature_coverage.py` according to the exact specifications below will completely eliminate all forensic integrity violations and enable clean `pytest tests/e2e/` execution.

---

## 3. Caveats

- **Test Database Isolation**: SQLite requires careful handling of transaction isolation. Test cases should use `django.test.TestCase` or `@pytest.mark.django_db(transaction=True)` when testing `transaction.atomic()` rollbacks (e.g. in `import_quran` tests) to prevent database lock contention.
- **Frontend Contract Validation**: Features 11–15 relate to frontend components. In the Python E2E suite, these should be validated by:
  1. Inspecting the authentic frontend source files on disk (`frontend/src/plugins/core/pluginTypes.ts`, `frontend/src/plugins/quran/manifest.ts`, `TopicMessageInput.vue`).
  2. Testing the corresponding backend REST endpoints, serializers, and formatter services that produce the exact JSON and Markdown payloads consumed by the frontend.

---

## 4. Conclusion & Concrete Remediation Plan

### Remediation Step 1: Update `tests/e2e/conftest.py`
In `tests/e2e/conftest.py`, add the `clean_db` override fixture to prevent `tests/conftest.py`'s `call_command('flush')` from running during SQLite execution:

```python
@pytest.fixture(autouse=True)
def clean_db():
    """
    Overrides the root tests/conftest.py clean_db fixture for all tests in tests/e2e/.
    Prevents call_command('flush') on SQLite which triggers content-type constraint errors.
    Isolation is handled safely by e2e_db_cleaner during teardown.
    """
    yield
```

### Remediation Step 2: Full Refactoring of `tests/e2e/test_tier1_feature_coverage.py`
Remove all local duplicate reference classes (`ReferenceManifestValidator`, `reference_normalize_quran_text`, etc.) and refactor all 18 feature classes (90 test cases) as follows:

```
+-------------------------------------------------------------------------------------------------------------+
| Feature | Class Name                               | Authentic Target Imported / Exercised                  | Key Validations in 5 Test Cases                                |
|:-------:|:-----------------------------------------|:-------------------------------------------------------|:----------------------------------------------------------------|
| F01     | TestTier1Feature01CorePluginModels       | apps.plugin_system.models.Plugin, Installation, etc.  | DB create, UUID PK, config merging, unique constraint, loose FK|
| F02     | TestTier1Feature02ManifestValidator      | apps.plugin_system.validator.ManifestValidator         | Real schema validation, version==1, regex, capabilities, scopes |
| F03     | TestTier1Feature03DynamicPluginRegistry  | apps.plugin_system.registry.PluginRegistry             | Autodiscover, load_plugin('plugins.quran'), sync_to_db, clear   |
| F04     | TestTier1Feature04SettingsIsolation      | settings.INSTALLED_TAFAKOR_PLUGINS, core models        | override_settings([]), autodiscover fallback, core ORM queries  |
| F05     | TestTier1Feature05PluginManagementAPIs   | DRF APIClient -> /api/plugins/*                        | GET marketplace, detail, POST install/toggle/uninstall, auth    |
| F06     | TestTier1Feature06MultiEditionQuranModels| plugins.quran.models.QuranEdition, Surah, Juz, Ayah   | ORM create, composite unique keys, revelation metadata, sajda   |
| F07     | TestTier1Feature07UnicodeNormalizerEngine| plugins.quran.services.normalizer.normalize_quran_text | Tashkeel, Dagger Alef, Alef/Yeh/Kaf unification, Tatweel strip |
| F08     | TestTier1Feature08AtomicJSONImporter     | call_command('import_quran', ...)                      | Ingest JSON dataset, --dry-run, atomic rollback on bad data, -f |
| F09     | TestTier1Feature09CrossDBSearchEngine    | plugins.quran.services.search_service.search_quran    | Exact phrase, multi-token AND, surah filter, <mark> highlight   |
| F10     | TestTier1Feature10QuranNavigationAPIs    | DRF APIClient -> /api/plugins/quran/*                  | GET editions, surahs, ayahs/1/1/, juzs, compare, format-ref    |
| F11     | TestTier1Feature11FrontendPluginCore     | backend/plugins/quran/manifest.json, frontend types    | Validate manifest against ManifestValidator, inspect TS types   |
| F12     | TestTier1Feature12DynamicLazyLoading     | Dynamic route definitions in manifest.json & views     | Route schemas, lazy-load views on disk, URL router isolation    |
| F13     | TestTier1Feature13MarketplaceUI          | DRF APIClient -> /api/plugins/?search=&capability=     | Query filtering by search & capability, settings_schema Draft-07|
| F14     | TestTier1Feature14QuranMiniAppViews      | DRF APIClient -> /api/plugins/quran/*                  | Catalog endpoint, reader endpoint with translation, audio URLs  |
| F15     | TestTier1Feature15ComposerActionIntegr.  | plugins.quran.services.formatter.format_quran_markdown  | Format single verse & range, inject in Post, content_hash save  |
| F16     | TestTier1Feature16OpaqueBoxE2ETestSuite  | tests/e2e/ files on disk, test_runner.build_parser     | os.path.exists on 4 tiers + runner, argparse parsing, DB isolat.|
| F17     | TestTier1Feature17CoreNonRegression      | apps.accounts.User, notes.Topic, Post, BotTask, Donation| Create real User (OTP/Token), Topic, Post, BotTask, Campaign   |
| F18     | TestTier1Feature18AdversarialHardening   | ManifestValidator, search_quran, import_quran, auth    | XSS/traversal injection, SQLi in search, extreme Unicode fuzz   |
+-------------------------------------------------------------------------------------------------------------+
```

### Detailed Code Blueprint for `tests/e2e/test_tier1_feature_coverage.py`

#### Header & Authentic Imports:
```python
import os
import sys
import json
import uuid
import tempfile
import pathlib
import pytest
from django.test import TestCase, override_settings
from django.core.management import call_command, CommandError
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from apps.accounts.models import User
from apps.notes.models import Topic, Post, TopicAdmin, BotTask
from apps.donations.models import DonationCampaign
from apps.plugin_system.models import Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference
from apps.plugin_system.validator import ManifestValidator
from apps.plugin_system.exceptions import ManifestValidationError, PluginRegistrationError
from apps.plugin_system.registry import PluginRegistry, plugin_registry
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.manifest import PluginManifest

from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah
from plugins.quran.services.normalizer import normalize_quran_text, strip_quranic_diacritics
from plugins.quran.services.search_service import search_quran, highlight_authentic_text, QuranSearchService
from plugins.quran.services.formatter import format_quran_markdown_reference, format_ayah_model_reference, QuranMarkdownFormatter
from tests.e2e.test_runner import build_parser
```

#### Detailed Test Case Specifications:

1. **Feature 01: Core Plugin Models (`TestTier1Feature01CorePluginModels`)**:
   - `test_f01_c01_plugin_model_creation_and_attributes`: `Plugin.objects.create(identifier="quran", name="قرآن کریم", version="1.0.0", capabilities=["composer_action"], manifest_version=1)`. Assert `isinstance(p.id, uuid.UUID)`, `p.has_capability("composer_action")`, `str(p) == "قرآن کریم (quran v1.0.0)"`.
   - `test_f01_c02_plugin_installation_user_uniqueness_and_config`: Create `PluginInstallation(user=user, plugin=plugin, user_config={"font_size": 20})`. Test `installation.get_effective_config()["font_size"] == 20`. Test creating duplicate `PluginInstallation` raises `django.db.IntegrityError`.
   - `test_f01_c03_plugin_topic_installation_lifecycle`: Create `PluginTopicInstallation(topic=topic, plugin=plugin, installed_by=user, topic_config={"pinned": 1})`. Test `installation.get_effective_config()["pinned"] == 1`. Toggle `installation.is_enabled = False; installation.save()`. Assert persisted in DB.
   - `test_f01_c04_post_plugin_reference_loose_coupling`: Create `PostPluginReference(post=post, plugin=plugin, resource_type="ayah", external_id="1:1", metadata={"surah": 1})`. Assert `isinstance(ref.external_id, str)`, query `post.plugin_references.count() == 1`.
   - `test_f01_c05_plugin_model_capability_and_scope_helpers`: Test `plugin.has_capability("composer_action") is True`, `plugin.has_capability("non_existent") is False`, `plugin.has_scope("read:quran") is True`.

2. **Feature 02: Manifest Validator (`TestTier1Feature02ManifestValidator`)**:
   - `test_f02_c01_valid_manifest_passes_validation`: Call `ManifestValidator.validate(valid_manifest)`. Assert returns normalized dict with `identifier == "quran"`, `manifest_version == 1`.
   - `test_f02_c02_manifest_version_must_be_one`: Pass `manifest_version` values `0, 2, 99, None, "1", True`. Assert `ManifestValidationError` raised in all cases.
   - `test_f02_c03_identifier_regex_validation`: Pass identifiers `"Quran", "quran plugin", "quran@v1", "", "UPPER"`. Assert `ManifestValidationError` raised.
   - `test_f02_c04_capabilities_and_scopes_whitelist`: Pass unknown capability `["unapproved_cap"]` or scope `["root:superadmin"]`. Assert `ManifestValidationError` raised with descriptive message.
   - `test_f02_c05_settings_schema_and_default_config_validation`: Pass `settings_schema="not-a-dict"` or `default_config=["not-a-dict"]`. Assert `ManifestValidationError` raised.

3. **Feature 03: Dynamic Plugin Registry (`TestTier1Feature03DynamicPluginRegistry`)**:
   - `test_f03_c01_registry_load_and_get_plugin`: Instantiate `registry = PluginRegistry()`. Register `BasePlugin(manifest=PluginManifest.from_dict(valid_manifest))`. Assert `registry.is_registered("quran") is True`, `registry.get("quran").name == "قرآن کریم"`.
   - `test_f03_c02_registry_filter_by_capability`: Register two plugins with different capabilities. Assert `registry.get_plugins_with_capability("composer_action")` returns only the matching plugin.
   - `test_f03_c03_registry_autodiscover_from_settings`: Call `registry.load_plugin("plugins.quran")`. Assert successfully registered.
   - `test_f03_c04_registry_sync_to_database`: Call `registry.sync_to_db()`. Assert `Plugin.objects.filter(identifier="quran").exists() is True`.
   - `test_f03_c05_registry_lifecycle_and_clear`: Register plugin, call `registry.clear()`. Assert `registry.get_all() == []` and `registry.is_registered("quran") is False`.

4. **Feature 04: Settings Isolation (`TestTier1Feature04SettingsIsolation`)**:
   - `test_f04_c01_empty_installed_tafakor_plugins_setting`: `@override_settings(INSTALLED_TAFAKOR_PLUGINS=[])`. Call `registry.autodiscover()`. Assert `registry.get_all() == []` without any startup crash.
   - `test_f04_c02_missing_setting_fallback`: Test `autodiscover()` when setting is missing; verify fallback to empty list.
   - `test_f04_c03_core_apps_unaffected_by_plugins`: With empty plugins, create `User`, `Topic`, `Post` in DB and assert queries succeed.
   - `test_f04_c04_invalid_plugin_app_path_resilience`: Test `registry.load_plugin("plugins.non_existent")` raises `PluginRegistrationError` gracefully.
   - `test_f04_c05_unmigrated_db_sync_resilience`: Test `registry.sync_to_db()` logs error gracefully when DB tables are absent.

5. **Feature 05: Plugin Management APIs (`TestTier1Feature05PluginManagementAPIs`)**:
   - `test_f05_c01_list_marketplace_plugins_api`: `client.get("/api/plugins/")`. Assert 200 OK, returns list containing active plugins.
   - `test_f05_c02_get_plugin_detail_api`: `client.get(f"/api/plugins/{plugin.identifier}/")`. Assert 200 OK, includes `settings_schema` and `default_config`.
   - `test_f05_c03_user_plugin_install_toggle_uninstall_api`: Authenticated `client`.
     - POST `/api/plugins/{id}/install/` -> 201 Created.
     - POST `/api/plugins/{id}/toggle/` -> 200 OK (`is_enabled` toggled).
     - POST `/api/plugins/{id}/uninstall/` -> 200 OK (`PluginInstallation` deleted).
   - `test_f05_c04_topic_plugin_install_toggle_uninstall_api`: Topic admin client.
     - POST `/api/plugins/topics/{topic.id}/install/` with `{"identifier": "quran"}` -> 201 Created.
     - POST `/api/plugins/topics/{topic.id}/toggle/` -> 200 OK.
     - POST `/api/plugins/topics/{topic.id}/uninstall/` -> 200 OK.
   - `test_f05_c05_plugin_api_authentication_and_permissions`:
     - Anonymous client calling POST `/api/plugins/{id}/install/` gets 401.
     - Non-admin client calling POST `/api/plugins/topics/{topic.id}/install/` gets 403.
     - Topic admin gets 201.

6. **Feature 06: Multi-Edition Quran Models (`TestTier1Feature06MultiEditionQuranModels`)**:
   - `test_f06_c01_quran_edition_model_fields_and_types`: Create `QuranEdition.objects.create(identifier="fa.ansarian", name="ترجمه انصاریان", language="fa", type="translation", direction="rtl", is_default=True)`. Assert persisted and `is_default is True`.
   - `test_f06_c02_quran_surah_model_metadata_and_revelation`: Create `QuranSurah.objects.create(number=1, name="الفاتحة", english_name="Al-Faatiha", revelation_type="Meccan", ayah_count=7, bismillah_pre=True)` and Surah 9 (`bismillah_pre=False`). Assert saved and filtered.
   - `test_f06_c03_quran_juz_boundary_and_mapping`: Create `QuranJuz.objects.create(number=1, start_surah=s1, start_ayah=1, end_surah=s2, end_ayah=141)`. Assert `juz.start_surah == s1`.
   - `test_f06_c04_quran_ayah_relationships_and_uniqueness`: Create `QuranAyah(edition=ed, surah=s1, number=1, number_in_surah=1, juz=1, text="...", normalized_text="...")`. Assert duplicate composite key raises `IntegrityError`.
   - `test_f06_c05_quran_ayah_sajda_and_metadata_json`: Create `QuranAyah` with `sajda={"recommended": True, "obligatory": False}`, `audio_url="https://..."`. Assert JSON fields serialize accurately.

7. **Feature 07: Unicode Normalizer Engine (`TestTier1Feature07UnicodeNormalizerEngine`)**:
   - `test_f07_c01_strips_arabic_tashkeel_and_harakat`: `normalize_quran_text("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ") == "بسم الله الرحمن الرحیم"`.
   - `test_f07_c02_strips_dagger_alef_and_quranic_stop_marks`: `normalize_quran_text("الرَّحْمَٰنِ عَلَّمَ الْقُرْآنَ ۚ") == "الرحمن علم القران"`.
   - `test_f07_c03_standardizes_all_alef_variants`: `normalize_quran_text("إِنَّا أَعْطَيْنَاكَ ٱلْكَوْثَرَ") == "انا اعطیناک الکوثر"`.
   - `test_f07_c04_standardizes_yeh_and_kaf_variants`: `normalize_quran_text("مَالِكِ يَوْمِ الدِّينِ") == "مالک یوم الدین"`.
   - `test_f07_c05_normalizes_tatweel_punctuation_and_whitespace`: `normalize_quran_text("  ﴿الْحَمْـــدُ لِلَّهِ رَبِّ الْعَالَمِينَ﴾  ۝  ") == "الحمد لله رب العالمین"`.

8. **Feature 08: Atomic JSON Importer (`TestTier1Feature08AtomicJSONImporter`)**:
   - `test_f08_c01_import_sample_dataset_success`: Generate temp JSON dataset with 3 ayahs, run `call_command('import_quran', '--file', path)`. Assert `QuranAyah.objects.count() == 3`.
   - `test_f08_c02_importer_dry_run_mode`: Run `call_command('import_quran', '--dry-run', '--file', path)`. Assert `QuranAyah.objects.count() == 0`.
   - `test_f08_c03_atomic_rollback_on_malformed_ayah`: Run `call_command('import_quran', '--file', corrupt_path)`. Assert `CommandError` raised and DB rolled back.
   - `test_f08_c04_importer_force_flag_idempotence`: Re-run with `--force`. Assert updates existing ayahs without duplicate key errors.
   - `test_f08_c05_importer_auto_populates_normalized_text`: Query imported `QuranAyah` and assert `ayah.normalized_text == normalize_quran_text(ayah.text)`.

9. **Feature 09: Cross-DB Search Engine (`TestTier1Feature09CrossDBSearchEngine`)**:
   - `test_f09_c01_exact_normalized_phrase_search`: Call `search_quran("الرحمن الرحيم")` and `search_quran("الرَّحْمَٰنِ الرَّحِيمِ")`. Assert results match authentic DB verses.
   - `test_f09_c02_multi_word_and_token_query`: Call `search_quran("الله رحمن")`. Assert returns ayahs containing all tokens.
   - `test_f09_c03_search_scoped_by_edition_and_surah`: Call `search_quran("الله", surah_number=112)`. Assert all results have `surah_number == 112`.
   - `test_f09_c04_authentic_text_and_highlighting_preservation`: `highlight_authentic_text("بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", ["الرحمن"])`. Assert `<mark>ٱلرَّحْمَٰنِ</mark>` returned.
   - `test_f09_c05_empty_query_and_no_match_resilience`: Search empty query and non-matching query. Assert `count == 0` and `results == []`.

10. **Feature 10: Quran Navigation APIs (`TestTier1Feature10QuranNavigationAPIs`)**:
    - `test_f10_c01_list_and_retrieve_editions_api`: `client.get("/api/plugins/quran/editions/")`. Assert 200 OK.
    - `test_f10_c02_list_surahs_and_ayahs_pagination_api`: `client.get("/api/plugins/quran/surahs/")` and `/api/plugins/quran/surahs/1/ayahs/`. Assert 200 OK.
    - `test_f10_c03_single_ayah_coordinate_api`: `client.get("/api/plugins/quran/ayahs/1/1/")`. Assert 200 OK.
    - `test_f10_c04_juz_navigation_and_ayahs_api`: `client.get("/api/plugins/quran/juzs/")` or `client.get("/api/plugins/quran/juz/1/")`. Assert 200 OK.
    - `test_f10_c05_parallel_compare_and_format_reference_api`: `client.get("/api/plugins/quran/compare/?surah=1&ayah=1&editions=quran-simple,fa.ansarian")` and `client.post("/api/plugins/quran/format-reference/", data={"surah": 1, "ayah_from": 1})`. Assert 200 OK and markdown output.

11. **Feature 11: Frontend Plugin Core (`TestTier1Feature11FrontendPluginCore`)**:
    - `test_f11_c01_frontend_manifest_contract_validation`: Load `backend/plugins/quran/manifest.json`. Validate with `ManifestValidator.validate(...)`.
    - `test_f11_c02_frontend_plugin_types_contract_exists`: Assert `frontend/src/plugins/core/pluginTypes.ts` exists on disk.
    - `test_f11_c03_frontend_capability_guard_evaluation`: Query `Plugin.objects.get(identifier='quran').has_capability('composer_action')`.
    - `test_f11_c04_frontend_error_boundary_component_exists`: Assert `frontend/src/plugins/core/PluginErrorBoundary.vue` exists on disk.
    - `test_f11_c05_frontend_registry_and_loader_exist`: Assert `frontend/src/plugins/core/pluginRegistry.ts` and `pluginLoader.ts` exist on disk.

12. **Feature 12: Dynamic Lazy-Loading (`TestTier1Feature12DynamicLazyLoading`)**:
    - `test_f12_c01_dynamic_routes_in_manifest`: Verify `backend/plugins/quran/manifest.json` defines routes array under `/apps/quran`.
    - `test_f12_c02_dynamic_loader_cache_contract`: Verify `frontend/src/plugins/core/pluginLoader.ts` contains cache handling.
    - `test_f12_c03_backend_router_isolation`: Verify `/api/plugins/` routes do not clash with core routes.
    - `test_f12_c04_lazy_views_exist_on_disk`: Verify `frontend/src/plugins/quran/views/` exists.
    - `test_f12_c05_no_eager_side_effects`: Verify importing plugin modules executes zero DB queries on import time.

13. **Feature 13: Marketplace UI (`TestTier1Feature13MarketplaceUI`)**:
    - `test_f13_c01_marketplace_api_schema`: `client.get("/api/plugins/")`. Verify keys (`identifier`, `name`, `capabilities`, `is_installed`).
    - `test_f13_c02_marketplace_capability_filter`: `client.get("/api/plugins/?capability=composer_action")`. Verify filtered list.
    - `test_f13_c03_marketplace_search_filter`: `client.get("/api/plugins/?search=quran")`. Verify filtered list.
    - `test_f13_c04_marketplace_view_component_exists`: Assert `frontend/src/views/FeedView.vue` exists.
    - `test_f13_c05_marketplace_settings_schema_renderer_contract`: Query `plugin.settings_schema` and verify Draft-07 schema compliance.

14. **Feature 14: Quran Mini-App Views (`TestTier1Feature14QuranMiniAppViews`)**:
    - `test_f14_c01_quran_surah_catalog_api`: `client.get("/api/plugins/quran/surahs/")`. Verify list of 114 surahs.
    - `test_f14_c02_quran_ayah_reader_api`: `client.get("/api/plugins/quran/surahs/1/ayahs/?edition=quran-simple&with_translation=fa.ansarian")`.
    - `test_f14_c03_quran_juz_reader_api`: `client.get("/api/plugins/quran/juzs/")`.
    - `test_f14_c04_quran_search_api`: `client.get("/api/plugins/quran/search/?q=الرحمن")`.
    - `test_f14_c05_quran_audio_stream_contract`: Query `QuranAyah` for audio URL field structure.

15. **Feature 15: Composer Action Integration (`TestTier1Feature15ComposerActionIntegration`)**:
    - `test_f15_c01_composer_action_in_manifest`: Verify `manifest.json` declares composer action `"id": "insert_ayah"`.
    - `test_f15_c02_verse_picker_format_endpoint`: `client.post("/api/plugins/quran/format-reference/", data={"surah": 1, "ayah_from": 1, "ayah_to": 1})`. Assert returns Markdown starting with `> ﴿`.
    - `test_f15_c03_markdown_formatting_verse_range`: Call `format_quran_markdown_reference(surah_name="الفاتحة", surah_number=1, ayah_from=1, ayah_to=2, arabic_texts=["...", "..."])`. Assert contains `۝۱` and citation.
    - `test_f15_c04_markdown_injection_preserves_post_text`: Verify injected markdown in user text preserves text structure.
    - `test_f15_c05_post_publishing_pipeline_untouched`: Create `Post.objects.create(topic=topic, author=user, content=formatted_md)`. Assert saved with `content_hash` without error.

16. **Feature 16: Opaque-Box E2E Test Suite (`TestTier1Feature16OpaqueBoxE2ETestSuite`)**:
    - `test_f16_c01_4tier_test_suite_files_exist`: Assert `Path("tests/e2e/test_tier1_feature_coverage.py").exists()`, `test_tier2_boundary_cases.py`, `test_tier3_pairwise_combinations.py`, `test_tier4_real_world_workloads.py`, `conftest.py`, `test_runner.py` all exist on disk.
    - `test_f16_c02_test_runner_cli_argument_parsing`: Call `build_parser().parse_args(["--tier", "1"])`. Assert `args.tier == ["1"]`. Call `--all` and `--non-regression`.
    - `test_f16_c03_test_isolation_and_db_cleanup`: Create DB entities and test cleanup without dummy `cleaned = True`.
    - `test_f16_c04_opaque_box_routes_resolvable`: Assert `reverse('plugin-marketplace-list')` and `reverse('quran-search')` resolve correctly.
    - `test_f16_c05_test_runner_dry_run_execution`: Execute `build_parser().parse_args(["--dry-run", "--all"])`.

17. **Feature 17: Core Non-Regression (`TestTier1Feature17CoreNonRegression`)**:
    - `test_f17_c01_accounts_user_model_and_auth`: Create `User.objects.create_user(phone="09121234567", password="password123")`. Verify `user.check_password("password123")` and `Token.objects.get_or_create(user=user)`.
    - `test_f17_c02_notes_topics_and_posts_non_regression`: Create `Topic.objects.create(name="Topic 1", created_by=user)` and `Post.objects.create(topic=topic, author=user, content="Post Content")`. Assert `post.content_hash` is computed.
    - `test_f17_c03_donations_campaign_creation`: Create `DonationCampaign.objects.create(topic=topic, creator=user, title="کمپین", target_amount=1000000)`. Assert `campaign.status == DonationCampaign.StatusChoices.ACTIVE`.
    - `test_f17_c04_bot_runner_task_creation`: Create `BotTask.objects.create(action="send", platform="telegram", chat_id="@chan", text="msg")`. Assert query `BotTask.objects.filter(processed=False).count() == 1`.
    - `test_f17_c05_post_retrieval_with_uninstalled_plugin`: Create `Post` with `PostPluginReference`. Deactivate/delete `Plugin`. Assert `Post` is retrieved 100% intact without foreign key errors.

18. **Feature 18: Adversarial Coverage Hardening (`TestTier1Feature18AdversarialCoverageHardening`)**:
    - `test_f18_c01_adversarial_malformed_manifest_payloads`: Pass malicious manifests (XSS tags, directory traversal `../../`, prototype pollution) to `ManifestValidator.validate(...)`. Assert `ManifestValidationError` is raised.
    - `test_f18_c02_adversarial_sql_injection_in_search`: Pass SQL injection strings (`' OR '1'='1`, `'; DROP TABLE tafakor_plugins; --`) to `search_quran(query=sqli)`. Assert queries execute safely through Django ORM without syntax crash.
    - `test_f18_c03_adversarial_extreme_unicode_fuzzing`: Pass stacked diacritics (`\u064e*100`), BiDi control codes, and ligature characters to `normalize_quran_text(...)`. Assert executes deterministically without exception.
    - `test_f18_c04_adversarial_unauthorized_topic_privilege_escalation`: Authenticate client as non-admin user. Send `POST /api/plugins/topics/{topic.id}/install/`. Assert returns 403 Forbidden.
    - `test_f18_c05_adversarial_importer_out_of_bounds_recovery`: Pass JSON with invalid surah number `999` to `call_command('import_quran', '--file', path)`. Assert `CommandError` is raised and transaction rolled back.

---

## 5. Verification Method

Once the changes are implemented by the Refactoring agent:

1. **Verify Test Harness Compatibility (SQLite `clean_db` Fixture Fix)**:
   ```bash
   pytest tests/e2e/test_tier1_feature_coverage.py -v
   ```
   *Expected Result*: All 90 test cases pass with **0 errors, 0 failures** (no `flush` UNIQUE constraint crashes).

2. **Verify CLI Test Runner Tier 1 Execution**:
   ```bash
   python tests/e2e/test_runner.py --tier 1
   ```
   *Expected Result*: Tier 1 suite executes and reports `PASSED` in summary table with exit code 0.

3. **Verify Elimination of Forensic Violations**:
   ```bash
   grep -n "cleaned = True" tests/e2e/test_tier1_feature_coverage.py
   grep -n "ReferenceManifestValidator" tests/e2e/test_tier1_feature_coverage.py
   grep -n "reference_normalize_quran_text" tests/e2e/test_tier1_feature_coverage.py
   grep -n "self.assertTrue(True)" tests/e2e/test_tier1_feature_coverage.py
   ```
   *Expected Result*: **Zero matches** across the entire file.

4. **Verify Core Platform Non-Regression Suite**:
   ```bash
   python backend/manage.py test apps.accounts apps.notes apps.donations
   ```
   *Expected Result*: 70/70 tests pass (100% OK).
