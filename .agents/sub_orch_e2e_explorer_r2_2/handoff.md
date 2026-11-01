# Tier 2 Boundary Cases Remediation Plan (Explorer 2)

**Track**: E2E Testing Track (Iteration 2)  
**Target File**: `tests/e2e/test_tier2_boundary_cases.py`  
**Role**: Remediation Specialist (Tier 2 Boundary Cases Refactoring)  
**Working Directory**: `f:\AVA\tafakor\.agents\sub_orch_e2e_explorer_r2_2`  

---

## 1. Observation

A complete forensic inspection of `tests/e2e/test_tier2_boundary_cases.py` (1,513 lines), the backend production codebase (`backend/apps/plugin_system/`, `backend/plugins/quran/`), and test execution traces revealed four core categories of forensic integrity violations and runtime faults:

### A. Local Contract Duplicate Classes (Facade Pattern / Pattern 2 & 4)
In `tests/e2e/test_tier2_boundary_cases.py`, lines 81–298 define 5 redundant local contract classes that duplicate and self-certify logic instead of testing production services:
1. **`BasePluginContract`** (`lines 81–102`): Local stub duplicating `apps.plugin_system.base.BasePlugin`.
2. **`ManifestValidatorContract`** (`lines 103–178`): Local validator class tested in `TestTier2Feature01` and `TestTier2Feature02` (lines 345, 444, 461, 477, 495, 508, 519, 535) instead of testing `apps.plugin_system.validator.ManifestValidator`.
3. **`DynamicPluginRegistryContract`** (`lines 180–222`): Local dictionary-backed registry tested in `TestTier2Feature03` (lines 549–591) instead of `apps.plugin_system.registry.PluginRegistry`.
4. **`QuranNormalizerContract`** (`lines 223–272`): Local regex normalizer tested in `TestTier2Feature06` (line 754), `TestTier2Feature07` (lines 772, 778, 788, 794, 803, 810), `TestTier2Feature09` (lines 901, 908, 915, 921, 928), and `TestTier2Feature18` (lines 1447, 1453) instead of `plugins.quran.services.normalizer.normalize_quran_text`.
5. **`QuranReferenceFormatterContract`** (`lines 273–298`): Local verse formatter tested in `TestTier2Feature10` (lines 979, 988, 999), `TestTier2Feature14` (line 1229), and `TestTier2Feature15` (lines 1256, 1267, 1279, 1292, 1304) instead of `plugins.quran.services.formatter.format_quran_markdown_reference`.

### B. Fallback `try...except (ImportError, Exception)` Blocks Hiding Real Models
Multiple test cases in `TestTier2Feature01CorePluginModelsBoundaries` wrap real Django ORM model tests in `try...except` blocks with silent fallback to dummy local dictionaries or mocks:
- `test_01_plugin_identifier_duplicate_uniqueness_boundary` (`lines 316–339`): Falls back to `registry = DynamicPluginRegistryContract()`.
- `test_03_plugin_installation_unique_together_boundary` (`lines 356–373`): Falls back to `user_installs = {}`.
- `test_04_plugin_topic_installation_unique_together_boundary` (`lines 376–393`): Falls back to `topic_installs = {}`.
- `test_05_plugin_cascade_deletion_boundary` (`lines 397–415`): Falls back to `self.assertTrue(Post.objects.filter(id=post.id).exists())` without testing `PluginInstallation` cascade.

### C. Self-Certifying Constant & Dictionary Assertions
- **F06 (`lines 725–749`)**: `test_01_surah_number_out_of_range_boundary` asserts `self.assertFalse(1 <= num <= 114)` over local integers; `test_04_quran_edition_identifier_uniqueness_boundary` asserts `self.assertIn(duplicate_id, editions)` on a local dictionary `editions["quran-simple"] = ...`.
- **F08 (`lines 840–871`)**: `test_02_importer_missing_required_dataset_keys_boundary` and `test_04_importer_out_of_range_surah_in_dataset_boundary` evaluate local Python boolean expressions without invoking Django management command `import_quran`.
- **F16 (`lines 1331–1368`)**: Asserts on local dictionaries `cli_options = {"--help": True}` without executing `tests/e2e/test_runner.py` CLI parser.
- **F18 (`lines 1496–1504`)**: `test_05_adversarial_post_plugin_reference_non_existent_external_id_boundary` asserts `self.assertEqual(ref_record["external_id"], "...")` on a local dictionary instead of creating a `PostPluginReference` ORM instance.

### D. SQLite Database Locking & Savepoint Contention
During test execution on SQLite:
1. When testing `IntegrityError` (e.g. duplicate plugin identifier or unique constraint violations), calling `Model.objects.create()` inside `django.test.TestCase` without an inner `with transaction.atomic():` breaks the outer savepoint transaction, resulting in `django.db.utils.OperationalError: database is locked` on subsequent queries.
2. Cross-test state pollution occurs if test classes share hardcoded user phone numbers (`09121111111`) across separate `setUp()` methods without clean teardowns.

---

## 2. Logic Chain

1. **Mandate**: `ORIGINAL_REQUEST.md` (Integrity Mode: `development`), `PROJECT.md`, and `TEST_INFRA.md` require opaque-box E2E testing of actual production components, strictly forbidding dummy implementations, in-memory duplicate contracts, and fake assertions.
2. **Production Existence**: Production modules in `backend/apps/plugin_system/` (`models.py`, `validator.py`, `registry.py`, `views.py`, `base.py`, `exceptions.py`) and `backend/plugins/quran/` (`models.py`, `services/normalizer.py`, `services/formatter.py`, `services/search_service.py`, `views.py`, `management/commands/import_quran.py`) are fully implemented and ready for genuine boundary testing.
3. **Root Cause**: The Tier 2 suite was initially written against local contracts (`*Contract`) during parallel development. These duplicate classes must be removed and replaced with direct imports from production modules.
4. **Boundary Value Coverage**: Boundary Value Analysis (BVA) requires testing 0, 1, max, max+1, -1, empty, None, type errors, unauthenticated requests, permission violations, and Unicode corner cases directly against the production ORM models, validation engine, search queries, management commands, and DRF views.
5. **Database Stability**: To ensure zero SQLite locking contention, every expected `IntegrityError` test must wrap the failing statement in `with transaction.atomic():`, and test user fixtures must use isolated, unique phone numbers with explicit teardown.

---

## 3. Caveats

- **Design-Only Constraint**: As an Explorer agent, this report provides the exact, line-by-line architectural blueprint and replacement plan. Implementation must be performed by the designated Worker.
- **Python 3.14 + Django 4.2 Test Client Compatibility**: The compatibility monkeypatch for Django's template context copying (`django_context.Context.__copy__`) must be retained at the top of the test file to avoid Python 3.14 context copy exceptions during DRF client error responses.
- **Pytest Harness Isolation**: In `tests/e2e/conftest.py`, the `@pytest.fixture(autouse=True) def clean_db(): yield` override must be maintained to prevent root `tests/conftest.py` from issuing `call_command('flush')` on SQLite.

---

## 4. Conclusion & Concrete Remediation Plan

### A. Contract Removal Specification
Delete lines 81–298 of `tests/e2e/test_tier2_boundary_cases.py` completely. Specifically remove:
- `BasePluginContract`
- `ManifestValidatorContract`
- `DynamicPluginRegistryContract`
- `QuranNormalizerContract`
- `QuranReferenceFormatterContract`

### B. Production Module Imports Specification
Replace all contract imports with authentic production symbols:
```python
# Django & DRF Core
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.db import IntegrityError, transaction
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

# Core App Models
from apps.notes.models import Topic, Post, PostReaction, PostComment, BotTask, TopicAdmin
from apps.accounts.models import MessagingTarget

# Generic Plugin System (apps.plugin_system)
from apps.plugin_system.models import (
    Plugin,
    PluginInstallation,
    PluginTopicInstallation,
    PostPluginReference,
)
from apps.plugin_system.validator import ManifestValidator
from apps.plugin_system.exceptions import (
    PluginSystemException,
    ManifestValidationError,
    PluginRegistrationError,
    PluginNotFoundError,
)
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.manifest import PluginManifest
from apps.plugin_system.registry import PluginRegistry, plugin_registry

# Official Quran Plugin (plugins.quran)
from plugins.quran.models import (
    QuranEdition,
    QuranSurah,
    QuranJuz,
    QuranAyah,
)
from plugins.quran.services.normalizer import (
    normalize_quran_text,
    strip_quranic_diacritics,
)
from plugins.quran.services.formatter import (
    format_quran_markdown_reference,
    format_ayah_model_reference,
    QuranMarkdownFormatter,
    to_persian_digits,
)
from plugins.quran.services.search_service import (
    search_quran,
    search_quran_ayahs,
    highlight_authentic_text,
    QuranSearchService,
)
```

---

### C. Class-by-Class Remediation Specification (All 18 Features)

```
+----------------------------------------------------------------------------------------------------+
|                               TIER 2 BOUNDARY REFACTORING MATRIX                                   |
+----+---------------------------------------------+------------------------------------------------+
| #  | Test Class                                  | Real Implementation Exercised                  |
+----+---------------------------------------------+------------------------------------------------+
| 01 | TestTier2Feature01CorePluginModelsBoundaries| Plugin, PluginInstallation, TopicInstall, PostRef
| 02 | TestTier2Feature02ManifestValidatorBoundaries| apps.plugin_system.validator.ManifestValidator |
| 03 | TestTier2Feature03DynamicPluginRegistryBnd  | apps.plugin_system.registry.PluginRegistry     |
| 04 | TestTier2Feature04SettingsIsolationBnd      | PluginRegistry.autodiscover() + Settings       |
| 05 | TestTier2Feature05PluginManagementAPIsBnd   | DRF APIClient (/api/plugins/*)                 |
| 06 | TestTier2Feature06MultiEditionQuranModelsBnd| QuranEdition, QuranSurah, QuranJuz, QuranAyah  |
| 07 | TestTier2Feature07UnicodeNormalizerBnd      | plugins.quran.services.normalizer              |
| 08 | TestTier2Feature08AtomicJSONImporterBnd     | manage.py import_quran command                 |
| 09 | TestTier2Feature09CrossDBSearchEngineBnd    | search_quran() + QuranAyah normalized_text     |
| 10 | TestTier2Feature10QuranNavigationAPIsBnd    | DRF APIClient (/api/plugins/quran/*)           |
| 11 | TestTier2Feature11FrontendPluginCoreBnd     | Frontend Manifest schemas & Error Boundary     |
| 12 | TestTier2Feature12DynamicLazyLoadingBnd     | Dynamic route collision & param boundaries     |
| 13 | TestTier2Feature13MarketplaceUIBnd          | Marketplace API filtering & auth payload shapes|
| 14 | TestTier2Feature14QuranMiniAppViewsBnd      | Quran views, missing translation fallbacks     |
| 15 | TestTier2Feature15ComposerActionIntegrBnd   | format_quran_markdown_reference + Post model   |
| 16 | TestTier2Feature16OpaqueBoxE2ETestSuiteBnd  | tests.e2e.test_runner CLI argparser & layout   |
| 17 | TestTier2Feature17CoreNonRegressionBnd      | Core /api/notes/, /api/accounts/ APIs, BotTask |
| 18 | TestTier2Feature18AdversarialCoverageBnd    | SQL injection, Unicode bomb, path traversal, FK|
+----+---------------------------------------------+------------------------------------------------+
```

#### Feature 01: Core Plugin Models (`TestTier2Feature01CorePluginModelsBoundaries`)
- **Target**: `apps.plugin_system.models` (`Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference`).
- **Tests**:
  1. `test_01_plugin_identifier_duplicate_uniqueness_boundary`:
     - Create `Plugin(identifier="unique-plugin-1", name="P1", manifest={"manifest_version": 1, "identifier": "unique-plugin-1", "name": "P1", "version": "1.0.0", "capabilities": [], "scopes": []})`.
     - In `with self.assertRaises(IntegrityError): with transaction.atomic(): Plugin.objects.create(identifier="unique-plugin-1", name="P2")`.
     - Eliminate all try/except fallback code.
  2. `test_02_plugin_identifier_empty_and_whitespace_boundary`:
     - Test `ManifestValidator.validate` with `"", "   ", None, "UPPERCASE", "plugin@bad"` -> asserts `ManifestValidationError`.
  3. `test_03_plugin_installation_unique_together_boundary`:
     - Create `PluginInstallation(user=self.user, plugin=plugin)`.
     - In `with self.assertRaises(IntegrityError): with transaction.atomic(): PluginInstallation.objects.create(user=self.user, plugin=plugin)`.
  4. `test_04_plugin_topic_installation_unique_together_boundary`:
     - Create `PluginTopicInstallation(topic=self.topic, plugin=plugin, installed_by=self.user)`.
     - In `with self.assertRaises(IntegrityError): with transaction.atomic(): PluginTopicInstallation.objects.create(topic=self.topic, plugin=plugin)`.
  5. `test_05_plugin_cascade_deletion_boundary`:
     - Create `Plugin`, `PluginInstallation`, `PostPluginReference` attached to `Post`.
     - `plugin.delete()`.
     - Assert `PluginInstallation` and `PostPluginReference` are deleted, while `Post` remains in DB.
  6. `test_06_post_plugin_reference_loose_coupling_boundary`:
     - Create real `PostPluginReference` with extreme boundary values for `external_id`: 255-character slug, Persian unicode `"سوره:۱:آیه:۱"`, arbitrary namespace `"custom:ext:99999"`, and nested `metadata={"tags": ["a", "b"], "coords": {"s": 1, "a": 1}}`.
     - Assert record successfully retrieved via ORM without foreign keys to plugin tables.

#### Feature 02: Manifest Validator (`TestTier2Feature02ManifestValidatorBoundaries`)
- **Target**: `apps.plugin_system.validator.ManifestValidator` & `ManifestValidationError`.
- **Tests**:
  1. `test_01_manifest_non_dict_and_none_inputs_boundary`: `None, [], "str", 123, True` -> raises `ManifestValidationError`.
  2. `test_02_manifest_missing_required_keys_boundary`: Iterate over each required key (`manifest_version`, `identifier`, `name`, `version`, `capabilities`, `scopes`), pop key, assert `ManifestValidationError`.
  3. `test_03_manifest_invalid_version_bounds`: `manifest_version` with `0, 2, -1, 99, "1", 1.5, None, False, True` -> raises `ManifestValidationError`.
  4. `test_04_manifest_invalid_identifier_syntax_boundary`: `"MyPlugin", "my plugin", "plugin@v1", "-hyphen", "", " ", "a"*105` -> raises `ManifestValidationError`.
  5. `test_05_manifest_unrecognized_capabilities_and_scopes_boundary`: Manifest with `capabilities=["root_access"]` or `scopes=["superuser:grant"]` -> raises `ManifestValidationError`.
  6. `test_06_manifest_malformed_settings_schema_boundary`: Manifest with `settings_schema="not_dict"` or `default_config="not_dict"` -> raises `ManifestValidationError`.

#### Feature 03: Dynamic Plugin Registry (`TestTier2Feature03DynamicPluginRegistryBoundaries`)
- **Target**: `apps.plugin_system.registry.PluginRegistry` & `apps.plugin_system.base.BasePlugin`.
- **Tests**:
  1. `test_01_registry_register_invalid_object_boundary`: Registering `None` or an object without a manifest raises `PluginRegistrationError` or `TypeError`.
  2. `test_02_registry_get_unregistered_and_empty_identifier_boundary`: `registry.get("")`, `registry.get(None)`, `registry.get("non_existent")` return `None`.
  3. `test_03_registry_is_registered_boundary`: `registry.is_registered("fake")` is `False`; returns `True` after registering a valid `BasePlugin` subclass.
  4. `test_04_registry_duplicate_registration_replacement_boundary`: Registering plugin instance V1 then V2 with same identifier replaces entry in `registry.get_all()` without duplicating list count.
  5. `test_05_registry_clear_and_isolation_boundary`: `registry.clear()` removes all plugins and manifests; `registry.get_all()` returns `[]`.

#### Feature 04: Settings Isolation (`TestTier2Feature04SettingsIsolationBoundaries`)
- **Target**: `PluginRegistry.autodiscover()` with `django.conf.settings.INSTALLED_TAFAKOR_PLUGINS`.
- **Tests**:
  1. `test_01_empty_installed_plugins_list_boundary`: `@override_settings(INSTALLED_TAFAKOR_PLUGINS=[])`: Autodiscover executes cleanly, registering 0 plugins without startup errors.
  2. `test_02_none_installed_plugins_fallback_boundary`: `@override_settings(INSTALLED_TAFAKOR_PLUGINS=None)`: Autodiscover handles `None` via fallback `getattr(settings, 'INSTALLED_TAFAKOR_PLUGINS', []) or []`.
  3. `test_03_non_existent_plugin_module_skip_boundary`: `@override_settings(INSTALLED_TAFAKOR_PLUGINS=["invalid.non.existent.module"])`: Autodiscover logs error, skips missing package, and proceeds without crashing.
  4. `test_04_core_apps_isolation_boundary`: Full CRUD operations on `Topic`, `Post`, `User` with zero active plugins in settings.
  5. `test_05_invalid_types_in_installed_plugins_boundary`: `@override_settings(INSTALLED_TAFAKOR_PLUGINS=[123, None, ""])`: Autodiscover handles non-string entries safely without throwing unhandled exceptions.

#### Feature 05: Plugin Management APIs (`TestTier2Feature05PluginManagementAPIsBoundaries`)
- **Target**: DRF Endpoints `/api/plugins/` (`PluginMarketplaceListView`, `PluginUserInstallView`, `PluginUserToggleView`, `PluginUserUninstallView`, `TopicPluginInstallView`, `TopicPluginToggleView`, `TopicPluginUninstallView`).
- **Tests**:
  1. `test_01_unauthenticated_user_access_returns_401_boundary`: Anonymous `APIClient` requests to install, toggle, or uninstall plugins return `401 Unauthorized`.
  2. `test_02_non_admin_topic_plugin_management_returns_403_boundary`: User B posting to `/api/plugins/topics/<topic_a_id>/install/` returns `403 Forbidden`.
  3. `test_03_non_existent_plugin_id_returns_404_boundary`: Authenticated client posting to `/api/plugins/fake_plugin_9999/install/` returns `404 Not Found`.
  4. `test_04_non_existent_topic_id_returns_404_boundary`: Authenticated client posting to `/api/plugins/topics/999999/install/` returns `404 Not Found`.
  5. `test_05_invalid_config_payload_returns_400_boundary`: Posting non-dict payload to install/toggle endpoints returns `400 Bad Request`.

#### Feature 06: Multi-Edition Quran Models (`TestTier2Feature06MultiEditionQuranModelsBoundaries`)
- **Target**: `plugins.quran.models` (`QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah`).
- **Tests**:
  1. `test_01_surah_number_boundary_and_validation`: Create `QuranSurah(number=1)` and `QuranSurah(number=114)`. Verify boundary properties (`ayah_count`, `page_start`, `page_end`, `juz_start`).
  2. `test_02_juz_number_boundary_and_mapping`: Create `QuranJuz(number=1)` and `QuranJuz(number=30)` with ForeignKeys to `QuranSurah`.
  3. `test_03_ayah_number_in_surah_boundary_values`: Create `QuranAyah` with `number_in_surah=1` and `number_in_surah=286` (maximum Surah Ayah count).
  4. `test_04_quran_edition_identifier_uniqueness_boundary`: Creating duplicate `QuranEdition(identifier="quran-simple")` inside `with self.assertRaises(IntegrityError): with transaction.atomic(): QuranEdition.objects.create(...)`.
  5. `test_05_ayah_extreme_text_length_and_unicode_boundary`: Create `QuranAyah` with Ayat al-Dayn (2:282, 1000+ characters) and verify `normalized_text` and query retrieval.

#### Feature 07: Unicode Normalizer Engine (`TestTier2Feature07UnicodeNormalizerEngineBoundaries`)
- **Target**: `plugins.quran.services.normalizer.normalize_quran_text` & `strip_quranic_diacritics`.
- **Tests**:
  1. `test_01_normalizer_empty_none_and_whitespace_boundary`: `None, "", "   ", "\t\t\n\r"` -> returns `""`.
  2. `test_02_normalizer_all_arabic_tashkeel_combinations_boundary`: `"بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"` -> returns `"بسم الله الرحمن الرحیم"`.
  3. `test_03_normalizer_quranic_pause_marks_and_glyphs_boundary`: Stop marks (`صلے, قلے, ج, لا, ۛ`), Sajda `۩`, Rub el Hizb `۞` stripped cleanly.
  4. `test_04_normalizer_persian_and_arabic_letter_unification_boundary`: `ي, ى, ئ` -> `ی`; `ك` -> `ک`; `أ, إ, آ, ٱ` -> `ا`; `ة` -> `ه`.
  5. `test_05_normalizer_tatweel_zwnj_and_bidi_controls_boundary`: Tatweel `ـ` removed, ZWNJ `\u200c` normalized to space, LRM/RLM/BOM removed.
  6. `test_06_normalizer_extreme_length_and_repeating_diacritics_boundary`: 10,000 repeating combining marks and diacritics executed in <5ms without recursion errors.

#### Feature 08: Atomic JSON Importer (`TestTier2Feature08AtomicJSONImporterBoundaries`)
- **Target**: `django.core.management.call_command('import_quran', ...)`.
- **Tests**:
  1. `test_01_importer_corrupted_json_syntax_boundary`: Pointing `--file` to a file with malformed JSON raises `CommandError`.
  2. `test_02_importer_missing_required_dataset_keys_boundary`: JSON file missing `'data'` array or `'license'` raises `CommandError`.
  3. `test_03_importer_non_existent_file_path_boundary`: Pointing `--file` to `/non/existent/path.json` raises `CommandError`.
  4. `test_04_importer_out_of_range_surah_in_dataset_boundary`: Dataset referencing `surah_number=999` raises `CommandError` and performs atomic rollback.
  5. `test_05_importer_dry_run_no_database_mutations_boundary`: Running with `--dry-run` validates successfully while persisting 0 ayahs to the database.

#### Feature 09: Cross-DB Search Engine (`TestTier2Feature09CrossDBSearchEngineBoundaries`)
- **Target**: `plugins.quran.services.search_service.search_quran` & `highlight_authentic_text`.
- **Tests**:
  1. `test_01_search_empty_and_whitespace_query_boundary`: Search with `""`, `"   "` -> returns `count=0`, empty `results=[]`.
  2. `test_02_search_single_character_query_boundary`: Search with `"ا"`, `"م"`, `"ق"` returns matches cleanly without ORM crash.
  3. `test_03_search_ultra_long_query_boundary`: Search with 1,000+ character string normalizes and executes without database error.
  4. `test_04_search_diacritic_only_query_boundary`: Search with `"ًٌٍَُِّْٰ"` normalizes to `""` and returns `count=0`.
  5. `test_05_search_punctuation_and_non_arabic_query_boundary`: Search with `"؟!.,:؛ 🔍"` returns `count=0` without crashing.
  6. `test_06_search_highlighting_with_complex_diacritics_boundary`: `highlight_authentic_text("بِسْمِ ٱللَّهِ", ["الله"])` wraps authentic word in `<mark>` while preserving diacritics.

#### Feature 10: Quran Navigation APIs (`TestTier2Feature10QuranNavigationAPIsBoundaries`)
- **Target**: DRF Endpoints `/api/plugins/quran/` (`QuranSurahListView`, `QuranSurahAyahsView`, `QuranAyahDetailView`, `QuranJuzListView`, `QuranSearchView`, `QuranFormatReferenceView`).
- **Tests**:
  1. `test_01_api_surah_out_of_range_returns_404_boundary`: `GET /api/plugins/quran/surahs/0/`, `/115/`, `/-1/`, `/9999/` -> returns `404 Not Found`.
  2. `test_02_api_juz_out_of_range_returns_404_boundary`: `GET /api/plugins/quran/juzs/0/`, `/31/`, `/-1/`, `/999/` -> returns `404 Not Found`.
  3. `test_03_api_ayah_detail_not_found_returns_404_boundary`: `GET /api/plugins/quran/ayahs/1/999/` -> returns `404 Not Found`.
  4. `test_04_api_format_reference_invalid_surah_returns_400_or_404`: `POST /api/plugins/quran/format-reference/` with non-existent surah 999 -> returns `404 Not Found` or `400 Bad Request`.
  5. `test_05_api_search_endpoint_empty_query_boundary`: `GET /api/plugins/quran/search/?q=` -> returns `400 Bad Request` or empty results safely.

#### Feature 11: Frontend Plugin Core (`TestTier2Feature11FrontendPluginCoreBoundaries`)
- **Target**: Frontend plugin interface contracts, manifest validation, Pinia store state schemas, and error boundaries.
- **Tests**:
  1. `test_01_frontend_manifest_null_or_empty_id_boundary`: Validates contract that frontend manifest without `id` or with empty string is rejected.
  2. `test_02_frontend_duplicate_plugin_id_registration_boundary`: Validates contract that re-registering an updated plugin version replaces the previous instance in registry map.
  3. `test_03_frontend_plugin_loader_unregistered_plugin_boundary`: Validates contract that loader attempting to load non-existent plugin ID returns `null`/error without unhandled rejection.
  4. `test_04_frontend_error_boundary_contract`: Validates contract that component errors inside plugin mini-app are captured by error boundary without crashing root application.
  5. `test_05_frontend_corrupted_localstorage_recovery_boundary`: Validates contract that corrupted localStorage configuration string falls back to empty dictionary.

#### Feature 12: Dynamic Lazy-Loading (`TestTier2Feature12DynamicLazyLoadingBoundaries`)
- **Target**: Frontend lazy loader routing boundaries and module resolution rules.
- **Tests**:
  1. `test_01_dynamic_route_collision_protection_boundary`: Validates that plugin route registration cannot overwrite core platform routes (`/`, `/login`, `/admin`, `/donate`, `/settings`, `/feed`).
  2. `test_02_dynamic_route_unregistration_on_disable_boundary`: Validates that disabling a plugin removes its registered `/apps/<pluginId>/*` route definitions.
  3. `test_03_dynamic_import_failure_fallback_boundary`: Validates that chunk load failure triggers retry mechanism or error view.
  4. `test_04_dynamic_route_malformed_path_parameters_boundary`: Validates route parameter boundaries (`"undefined"`, `"null"`, `"NaN"`, `"-5"`, `"99999"`).
  5. `test_05_dynamic_import_concurrency_mutex_boundary`: Validates contract that concurrent import calls share a single pending Promise.

#### Feature 13: Marketplace UI (`TestTier2Feature13MarketplaceUIBoundaries`)
- **Target**: Marketplace REST contract under edge case queries.
- **Tests**:
  1. `test_01_marketplace_empty_catalog_state_boundary`: `GET /api/plugins/?search=non_existent_query_9999` -> returns empty list `[]` with status `200 OK`.
  2. `test_02_marketplace_capability_filter_empty_boundary`: `GET /api/plugins/?capability=non_existent_capability` -> returns empty list `[]` with status `200 OK`.
  3. `test_03_marketplace_authenticated_vs_anonymous_response_shape`: Verifies `/api/plugins/` payload for authenticated user includes `is_installed`, `is_enabled`, `user_config`, while anonymous user returns `is_installed=False`.
  4. `test_04_marketplace_rapid_toggle_debounce_boundary`: Simulates idempotent toggle requests.
  5. `test_05_marketplace_settings_schema_serialization`: Verifies `settings_schema` and `default_config` JSON fields serialize correctly in marketplace API.

#### Feature 14: Quran Mini-App Views (`TestTier2Feature14QuranMiniAppViewsBoundaries`)
- **Target**: Quran Mini-App views and formatter fallback contracts.
- **Tests**:
  1. `test_01_view_invalid_surah_id_navigation_boundary`: Surah URL parameter out of range (0, 115, -1, 999) handled with `404 Not Found`.
  2. `test_02_view_invalid_juz_id_navigation_boundary`: Juz URL parameter out of range (0, 31, -1, 100) handled with `404 Not Found`.
  3. `test_03_view_missing_translation_fallback_boundary`: When requesting Surah ayahs with non-existent translation ID, original Arabic ayahs are returned with `_translation_data = None` without crashing.
  4. `test_04_view_audio_stream_url_metadata_boundary`: `QuranAyah` with `audio_url=None` serializes cleanly with `null` audio URL.
  5. `test_05_view_massive_ayah_text_formatting_boundary`: Real `format_quran_markdown_reference` formatting ultra-long verse (Ayat al-Dayn) produces valid Markdown blockquote.

#### Feature 15: Composer Action Integration (`TestTier2Feature15ComposerActionIntegrationBoundaries`)
- **Target**: `plugins.quran.services.formatter` (`format_quran_markdown_reference`, `QuranMarkdownFormatter`, `to_persian_digits`) & `apps.plugin_system.models.PostPluginReference`.
- **Tests**:
  1. `test_01_composer_action_empty_verse_selection_boundary`: Calling `format_quran_markdown_reference(arabic_texts=[])` returns `""`.
  2. `test_02_composer_action_reverse_verse_range_boundary`: Calling `format_quran_markdown_reference(ayah_from=10, ayah_to=5, ...)` produces clean coordinates.
  3. `test_03_composer_action_markdown_special_characters_escaping_boundary`: Formatting verse with special Markdown characters (`*`, `_`, `[`, `]`, `<script>`) inside translation creates valid blockquote without corrupting markup.
  4. `test_04_composer_action_multi_verse_range_formatting_boundary`: Multi-verse selection produces proper citation header with Persian digits (e.g. `۱-۵`).
  5. `test_05_composer_action_non_invasive_post_creation_boundary`: Creates a real `Post` with formatted Markdown and links a real `PostPluginReference(resource_type='ayah', external_id='1:1')`, verifying zero changes to core `Post` model.

#### Feature 16: Opaque-Box E2E Test Suite (`TestTier2Feature16OpaqueBoxE2ETestSuiteBoundaries`)
- **Target**: `tests.e2e.test_runner` CLI argument parsing and test layout verification.
- **Tests**:
  1. `test_01_test_runner_tier_argument_parsing_boundaries`: Tests `parse_args(['--tier', '2'])`, `parse_args(['--tier', 'all'])`, `parse_args(['--all'])`.
  2. `test_02_test_runner_invalid_tier_flag_boundary`: Tests `parse_args(['--tier', '99'])` -> exits with error code or raises `SystemExit`.
  3. `test_03_test_runner_file_existence_boundary`: Validates that all 4 tier test files (`test_tier1_feature_coverage.py`, `test_tier2_boundary_cases.py`, `test_tier3_pairwise_combinations.py`, `test_tier4_real_world_workloads.py`) physically exist on disk in `tests/e2e/`.
  4. `test_04_test_runner_report_json_schema_boundary`: Validates that test runner JSON report schema conforms to standard structure (`total`, `passed`, `failed`, `errors`, `duration`).
  5. `test_05_test_runner_help_flag_boundary`: Tests `parse_args(['--help'])` raises `SystemExit(0)`.

#### Feature 17: Core Non-Regression (`TestTier2Feature17CoreNonRegressionBoundaries`)
- **Target**: Core platform endpoints (`/api/notes/`, `/api/accounts/`) and models (`Topic`, `Post`, `BotTask`).
- **Tests**:
  1. `test_01_core_topic_creation_empty_name_boundary`: `POST /api/notes/topics/` with `name=""` returns `400 Bad Request`.
  2. `test_02_core_post_creation_invalid_topic_boundary`: `POST /api/notes/` with `topic=999999` returns `400 Bad Request`.
  3. `test_03_core_user_registration_invalid_phone_boundaries`: `POST /api/accounts/otp/send/` with invalid phones (`"123"`, `"0912"`, `"abcdef"`, `""`) returns `400 Bad Request`.
  4. `test_04_core_comment_on_non_existent_post_boundary`: `POST /api/notes/999999/comments/` returns `404 Not Found`.
  5. `test_05_core_bot_task_special_characters_payload_boundary`: Create real `BotTask` with Persian text, emojis, and special quotes, asserting full fidelity.

#### Feature 18: Adversarial Coverage Hardening (`TestTier2Feature18AdversarialCoverageHardeningBoundaries`)
- **Target**: Security boundaries (SQL injection, Unicode bomb, path traversal, user cascade isolation, loose coupling).
- **Tests**:
  1. `test_01_adversarial_sql_injection_in_search_query_boundary`: Executes real `search_quran` with SQL injection payloads (`"' OR '1'='1"`, `"'; DROP TABLE notes_post; --"`, `"1 UNION SELECT NULL, NULL--"`) and asserts safe query execution without syntax error.
  2. `test_02_adversarial_unicode_bomb_in_normalizer_boundary`: Executes real `normalize_quran_text` on 10,000 repeating combining marks / ZWNJ characters, verifying sub-millisecond execution.
  3. `test_03_adversarial_manifest_directory_traversal_identifier_boundary`: Executes real `ManifestValidator.validate` on traversal identifiers (`"../../etc/passwd"`, `"/absolute/root"`, `"..\\..\\windows"`) -> raises `ManifestValidationError`.
  4. `test_04_adversarial_user_cascade_deletion_integrity_boundary`: Creates two real users with topics, deletes User A, verifies User B and User B's topics remain completely unaffected.
  5. `test_05_adversarial_post_plugin_reference_non_existent_external_id_boundary`: Creates a real `PostPluginReference` with non-existent / arbitrary `external_id="quran:ayah:999:99999"` linked to real `Plugin` and `Post`, asserting DB persistence and verifying loose coupling.

---

### D. SQLite Lock Prevention & DB Isolation Blueprint

To eliminate SQLite locking errors during local testing on Windows:

1. **Inner Atomic Savepoints**:
   Whenever testing an expected database exception (e.g. `IntegrityError`), ALWAYS use nested atomic transaction context:
   ```python
   with self.assertRaises(IntegrityError):
       with transaction.atomic():
           Plugin.objects.create(identifier="duplicate")
   ```
2. **Unique Fixture Data**:
   Each test class `setUp()` must use unique user phone numbers:
   - `TestTier2Feature01`: `09110010001`
   - `TestTier2Feature04`: `09110040001`
   - `TestTier2Feature05`: `09110050001`, `09110050002`
   - `TestTier2Feature15`: `09110150001`
   - `TestTier2Feature17`: `09110170001`
   - `TestTier2Feature18`: `09110180001`, `09110180002`
3. **Explicit Teardown Cleanup**:
   In `tearDown(self)`, clear in-memory registries via `plugin_registry.clear()` to prevent state leakage between tests.

---

## 5. Verification Method

Once implemented by the worker, the remediation must be verified with the following commands:

1. **Verify No Duplicate Contracts Exist**:
   ```bash
   grep -n "class BasePluginContract" tests/e2e/test_tier2_boundary_cases.py
   grep -n "class ManifestValidatorContract" tests/e2e/test_tier2_boundary_cases.py
   grep -n "class DynamicPluginRegistryContract" tests/e2e/test_tier2_boundary_cases.py
   grep -n "class QuranNormalizerContract" tests/e2e/test_tier2_boundary_cases.py
   grep -n "class QuranReferenceFormatterContract" tests/e2e/test_tier2_boundary_cases.py
   ```
   *Expected Output*: 0 matches.

2. **Verify Real Production Imports**:
   ```bash
   grep -n "from apps.plugin_system" tests/e2e/test_tier2_boundary_cases.py
   grep -n "from plugins.quran" tests/e2e/test_tier2_boundary_cases.py
   ```
   *Expected Output*: Direct imports of `ManifestValidator`, `PluginRegistry`, `QuranEdition`, `QuranAyah`, `normalize_quran_text`, `format_quran_markdown_reference`.

3. **Execute Tier 2 Test Suite**:
   ```bash
   python -m unittest tests/e2e/test_tier2_boundary_cases.py
   ```
   *Expected Output*: `Ran 90+ tests -> OK` (100% Passed, 0 errors, 0 failures, 0 database locks).

4. **Execute Unified Test Runner for Tier 2**:
   ```bash
   python tests/e2e/test_runner.py --tier 2
   ```
   *Expected Output*: Exit code 0, 100% pass rate.
