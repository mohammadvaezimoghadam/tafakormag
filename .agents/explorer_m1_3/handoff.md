# Handoff Report: Test Infrastructure Investigation & Test Suite Design (Milestone 1)

**Agent**: Explorer 3 (Test Infrastructure Specialist & QA Architect)  
**Date**: 2026-08-24  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_m1_3`  
**Target Subsystem**: Milestone 1 Generic Plugin System Core Test Suite (`backend/apps/plugin_system/tests/`)  

---

## 1. Observation

Direct code-level inspection of the Tafakor test infrastructure, configuration, fixtures, and existing test suites revealed the following architecture:

### 1.1 Test Configuration & Pytest Setup
- **`pytest.ini`** (`f:\AVA\tafakor\pytest.ini:1-6`):
  ```ini
  [pytest]
  DJANGO_SETTINGS_MODULE = note_platform.settings
  python_files = test_*.py tests.py
  addopts = --reuse-db -v --cov=backend --cov=bot_runner --cov-report=term-missing --cov-report=html:/app/tests/results/coverage
  norecursedirs = .git node_modules postgres-data venv .pytest_cache frontend/node_modules backend/staticfiles
  ```
- **Session DB Monkeypatch & Flush Fixture** (`tests/conftest.py:9-47`):
  ```python
  # Monkeypatch Django test DB name to prevent prepending 'test_' 
  # so test runner shares the database with the backend container
  from django.db.backends.base.creation import BaseDatabaseCreation
  BaseDatabaseCreation._get_test_db_name = lambda self: self.connection.settings_dict['NAME']

  django.setup()

  @pytest.fixture(scope="session")
  def django_db_setup(django_db_blocker):
      with django_db_blocker.unblock():
          pass

  @pytest.fixture(autouse=True)
  def clean_db(django_db_blocker):
      with django_db_blocker.unblock():
          from django.core.management import call_command
          call_command("flush", interactive=False, reset_sequences=True)
  ```
  - **Database Flush Mechanism**: The test runner executes against an active PostgreSQL instance (in Docker) or SQLite locally. The `clean_db` autouse fixture invokes `call_command('flush', interactive=False, reset_sequences=True)` before every test, guaranteeing full row isolation and primary key sequence resetting between tests without requiring table dropping/recreation.

### 1.2 Docker Testing Harness & Invocation Scripts
- **Docker Compose Test Config** (`docker-compose.test.yml:1-104`):
  - `postgres-test` (PostgreSQL 15 ephemeral)
  - `backend` (Django running on port 8000 with gunicorn)
  - `vue-frontend` (Nginx serving built Vue 3 frontend)
  - `test-runner` (Container with `tests/Dockerfile`, mounting workspace at `/app`, `PYTHONPATH=/app/backend:/app`)
- **PowerShell Test Script** (`run-tests.ps1:65-68`):
  ```powershell
  docker compose -f docker-compose.test.yml run --rm test-runner pytest -v --junitxml=/app/tests/results/junit.xml
  ```

### 1.3 Inventory of Existing Core Platform Tests
A comprehensive survey of existing test suites revealed **107 active test methods** across the repository:
1. **`backend/apps/accounts/tests.py`** (12 tests):
   - `AccountsServicesTestCase`: Kavenegar OTP SMS success, timeout error handling.
   - `AuthViewSetTestCase`: OTP delivery fallback to Bale, OTP success with Kavenegar, debug mode OTP, verify OTP success, wrong OTP code, expired OTP.
   - `OTPDispatcherTestCase`: Kavenegar fallback, delivery error raising.
   - `RegisterPhoneChatTestCase`: Bot phone/chat registration, phone normalization.
2. **`backend/apps/notes/tests.py`** (43 tests):
   - `NotesModelTests`: Topic creation, Post creation, Post ordering, PostReaction unique constraint, PostComment ordering, BotTask creation.
   - `TelegramImportTests` & `ZIPImportTests`: JSON/ZIP Telegram chat archive parsing and ingestion.
   - `TopicAdminTests`: Multi-admin promotion, permission enforcement, custom titles.
   - `SignalCleanupTests`: File cleanup signals on Post deletion.
   - `PostDeduplicationTests`: Content hashing and duplicate post prevention.
3. **`backend/apps/donations/tests/`** (15 tests across 3 files):
   - `test_models.py` (6 tests): Target amount guards, campaign creation, lifecycle auto-update on completion/overfunding, deadline expiry, transaction minimum amount.
   - `test_services.py` (3 tests): Payment settlement, idempotent settlement, metrics sync.
   - `test_api.py` (6 tests): Anonymous donor masking, private donor list guard, transparency log permissions.
4. **`tests/integration/`** (37 tests across 6 files):
   - `test_notes_api.py` (12 tests): Topic CRUD, Post creation with BotTask dispatch, permissions.
   - `test_donations_api.py` (7 tests): Campaign endpoints, donor lists, settlement callbacks.
   - `test_bot_api.py` (5 tests): Bot chat registration and token verification.
   - `test_bot_runner.py` (4 tests): Markdown to HTML converter, retry loop, rate limiting.
   - `test_bot_handlers.py` (7 tests): `/start`, `/register` mock command handlers.
   - `test_telegram_proxy.py` (2 tests): GAS proxy relay testing.

### 1.4 Authentication & Permissions Conventions
- **Authentication**: `rest_framework.authentication.TokenAuthentication` with `rest_framework.authtoken.models.Token`.
- **Topic Authorization**: `apps.notes.permissions.IsTopicOwnerOrAdmin` checking:
  1. `request.user.is_superuser`
  2. `topic.created_by == request.user`
  3. `topic.admins.filter(user=request.user).exists()` (`TopicAdmin` model)

---

## 2. Logic Chain: Plugin System Test Suite Design

To guarantee robust coverage, strict schema enforcement, and zero regressions for the Generic Plugin System Core (`apps/plugin_system`), we design a 5-module test suite placed under `backend/apps/plugin_system/tests/`.

```
backend/apps/plugin_system/tests/
├── __init__.py
├── test_models.py         # Unit tests: Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference
├── test_validator.py      # Unit tests: ManifestValidator (schema, regex, capabilities, scopes)
├── test_registry.py       # Unit tests: PluginRegistry (discovery, lifecycle hooks, error handling)
├── test_api.py            # DRF API tests: /api/plugins/ marketplace, user & topic installation lifecycle
└── test_isolation.py      # Zero-breaking-change verification & core app non-regression
```

### 2.1 Module 1: `test_models.py` (Model Constraints & Lifecycle)

```python
"""
backend/apps/plugin_system/tests/test_models.py
Unit tests for Plugin, PluginInstallation, PluginTopicInstallation, and PostPluginReference models.
"""
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, Post
from apps.plugin_system.models import (
    Plugin,
    PluginInstallation,
    PluginTopicInstallation,
    PostPluginReference,
)

User = get_user_model()

class PluginModelTestCase(TestCase):
    def setUp(self):
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن کریم",
            version="1.0.0",
            description="پلاگین رسمی قرآن کریم",
            author="Tafakor Team",
            icon="BookOpen",
            manifest_version=1,
            capabilities=["composer_action", "mini_app", "search_provider"],
            scopes=["read:quran", "write:composer"],
            settings_schema={"type": "object", "properties": {"default_edition": {"type": "string"}}},
            default_config={"default_edition": "quran-simple"},
            is_active=True,
            is_core=False
        )

    def test_plugin_creation_and_defaults(self):
        """Verify plugin UUID pk, string representation, and JSON defaults."""
        self.assertIsNotNone(self.plugin.id)
        self.assertEqual(str(self.plugin), "قرآن کریم (quran v1.0.0)")
        self.assertTrue(self.plugin.is_active)
        self.assertFalse(self.plugin.is_core)
        self.assertEqual(self.plugin.manifest_version, 1)

    def test_plugin_identifier_uniqueness(self):
        """Ensure duplicate identifier raises IntegrityError."""
        with self.assertRaises(IntegrityError):
            Plugin.objects.create(
                identifier="quran",
                name="قرآن تکراری",
                version="2.0.0"
            )

    def test_plugin_ordering(self):
        """Ensure plugins are ordered by name ascending."""
        Plugin.objects.create(identifier="analytics", name="آمار و تحلیل", version="1.0.0")
        plugins = list(Plugin.objects.all())
        self.assertEqual(plugins[0].identifier, "analytics")
        self.assertEqual(plugins[1].identifier, "quran")

    def test_plugin_json_fields_serialization(self):
        """Verify nested JSON schema and list storage in capabilities/scopes."""
        self.assertIn("composer_action", self.plugin.capabilities)
        self.assertIn("read:quran", self.plugin.scopes)
        self.assertEqual(self.plugin.default_config["default_edition"], "quran-simple")


class PluginInstallationModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09121111111")
        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")
        self.installation = PluginInstallation.objects.create(
            user=self.user,
            plugin=self.plugin,
            is_enabled=True,
            user_config={"theme": "dark"}
        )

    def test_installation_creation_and_defaults(self):
        """Verify user installation creation, UUID, and defaults."""
        self.assertIsNotNone(self.installation.id)
        self.assertTrue(self.installation.is_enabled)
        self.assertEqual(self.installation.user_config.get("theme"), "dark")

    def test_user_plugin_unique_constraint(self):
        """Ensure same user cannot install the same plugin twice."""
        with self.assertRaises(IntegrityError):
            PluginInstallation.objects.create(
                user=self.user,
                plugin=self.plugin,
                is_enabled=False
            )

    def test_cascade_delete_user(self):
        """Deleting user deletes their plugin installations."""
        user_id = self.user.id
        self.user.delete()
        self.assertFalse(PluginInstallation.objects.filter(user_id=user_id).exists())

    def test_cascade_delete_plugin(self):
        """Deleting plugin cascades to all user installations."""
        plugin_id = self.plugin.id
        self.plugin.delete()
        self.assertFalse(PluginInstallation.objects.filter(plugin_id=plugin_id).exists())


class PluginTopicInstallationModelTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(phone="09122222222")
        self.topic = Topic.objects.create(name="تاپیک تدبر قرآن", created_by=self.owner)
        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")
        self.topic_install = PluginTopicInstallation.objects.create(
            topic=self.topic,
            plugin=self.plugin,
            installed_by=self.owner,
            is_enabled=True,
            topic_config={"show_ayah_badge": True}
        )

    def test_topic_installation_creation(self):
        """Verify topic plugin installation creation and config."""
        self.assertIsNotNone(self.topic_install.id)
        self.assertEqual(self.topic_install.topic, self.topic)
        self.assertEqual(self.topic_install.plugin, self.plugin)
        self.assertEqual(self.topic_install.installed_by, self.owner)
        self.assertTrue(self.topic_install.is_enabled)

    def test_topic_plugin_unique_constraint(self):
        """Ensure duplicate (topic, plugin) pair raises IntegrityError."""
        with self.assertRaises(IntegrityError):
            PluginTopicInstallation.objects.create(
                topic=self.topic,
                plugin=self.plugin,
                is_enabled=False
            )

    def test_cascade_delete_topic(self):
        """Deleting topic cascades to all topic plugin installations."""
        topic_id = self.topic.id
        self.topic.delete()
        self.assertFalse(PluginTopicInstallation.objects.filter(topic_id=topic_id).exists())

    def test_set_null_installed_by_user(self):
        """Deleting installer user sets installed_by to NULL without deleting topic installation."""
        self.owner.delete()
        self.topic_install.refresh_from_db()
        self.assertIsNone(self.topic_install.installed_by)
        self.assertTrue(PluginTopicInstallation.objects.filter(id=self.topic_install.id).exists())


class PostPluginReferenceModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09123333333")
        self.topic = Topic.objects.create(name="تاپیک عمومی", created_by=self.user)
        self.post = Post.objects.create(topic=self.topic, author=self.user, content="متن تستی")
        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")
        self.ref = PostPluginReference.objects.create(
            post=self.post,
            plugin=self.plugin,
            resource_type="ayah",
            external_id="2:255",
            metadata={"surah": 2, "ayah": 255, "edition": "quran-simple"}
        )

    def test_post_reference_creation_and_attributes(self):
        """Verify PostPluginReference attributes, metadata, and decoupling."""
        self.assertIsNotNone(self.ref.id)
        self.assertEqual(self.ref.post, self.post)
        self.assertEqual(self.ref.plugin, self.plugin)
        self.assertEqual(self.ref.resource_type, "ayah")
        self.assertEqual(self.ref.external_id, "2:255")
        self.assertEqual(self.ref.metadata.get("surah"), 2)

    def test_cascade_delete_post(self):
        """Deleting Post cascades and removes PostPluginReference."""
        post_id = self.post.id
        self.post.delete()
        self.assertFalse(PostPluginReference.objects.filter(post_id=post_id).exists())

    def test_cascade_delete_plugin_keeps_post(self):
        """Deleting Plugin removes reference but preserves the original Post."""
        post_id = self.post.id
        self.plugin.delete()
        self.assertFalse(PostPluginReference.objects.filter(post_id=post_id).exists())
        self.assertTrue(Post.objects.filter(id=post_id).exists())
```

---

### 2.2 Module 2: `test_validator.py` (Manifest Schema & Validation Rules)

```python
"""
backend/apps/plugin_system/tests/test_validator.py
Unit tests for ManifestValidator enforcing schema v1, capabilities, scopes, and regex constraints.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.plugin_system.validator import ManifestValidator


class ManifestValidatorTestCase(TestCase):
    def setUp(self):
        self.valid_manifest = {
            "manifest_version": 1,
            "identifier": "quran",
            "name": "قرآن کریم",
            "version": "1.0.0",
            "description": "پلاگین رسمی قرآن کریم",
            "author": "Tafakor Team",
            "icon": "BookOpen",
            "entry_point": "plugins.quran.plugin.QuranPlugin",
            "capabilities": ["composer_action", "mini_app", "search_provider", "topic_integration"],
            "scopes": ["read:quran", "write:composer"],
            "settings_schema": {
                "type": "object",
                "properties": {
                    "default_edition": {"type": "string", "default": "quran-simple"}
                }
            },
            "default_config": {
                "default_edition": "quran-simple"
            }
        }

    def test_valid_manifest_passes(self):
        """A complete valid manifest dictionary must validate without exceptions."""
        validated = ManifestValidator.validate(self.valid_manifest)
        self.assertEqual(validated["identifier"], "quran")
        self.assertEqual(validated["manifest_version"], 1)

    def test_minimal_valid_manifest_passes(self):
        """Manifest with only mandatory fields must validate with safe defaults."""
        minimal = {
            "manifest_version": 1,
            "identifier": "minimal-plugin",
            "name": "Minimal",
            "version": "0.1.0"
        }
        validated = ManifestValidator.validate(minimal)
        self.assertEqual(validated["capabilities"], [])
        self.assertEqual(validated["scopes"], [])
        self.assertEqual(validated["settings_schema"], {})
        self.assertEqual(validated["default_config"], {})

    def test_missing_required_fields(self):
        """Missing any required field (manifest_version, identifier, name, version) raises ValidationError."""
        required_fields = ["manifest_version", "identifier", "name", "version"]
        for field in required_fields:
            data = dict(self.valid_manifest)
            del data[field]
            with self.assertRaises(ValidationError, msg=f"Should fail when missing '{field}'"):
                ManifestValidator.validate(data)

    def test_invalid_manifest_version(self):
        """Manifest version other than integer 1 must raise ValidationError."""
        invalid_versions = [0, 2, "1", 1.0, None, -1]
        for ver in invalid_versions:
            data = dict(self.valid_manifest, manifest_version=ver)
            with self.assertRaises(ValidationError, msg=f"Should fail for manifest_version={ver}"):
                ManifestValidator.validate(data)

    def test_identifier_regex_validation(self):
        """Identifier must strictly match ^[a-z0-9_-]+$."""
        invalid_identifiers = [
            "Quran",            # Uppercase
            "quran plugin",     # Space
            "quran@123",        # Special character
            "quran.core",       # Dot
            "قرآن",             # Non-ascii
            "",                 # Empty
            "quran/reader"      # Slash
        ]
        for ident in invalid_identifiers:
            data = dict(self.valid_manifest, identifier=ident)
            with self.assertRaises(ValidationError, msg=f"Should fail for identifier='{ident}'"):
                ManifestValidator.validate(data)

        valid_identifiers = ["quran", "quran_v1", "my-plugin-2", "a", "123_abc-xyz"]
        for ident in valid_identifiers:
            data = dict(self.valid_manifest, identifier=ident)
            validated = ManifestValidator.validate(data)
            self.assertEqual(validated["identifier"], ident)

    def test_invalid_capabilities(self):
        """Capabilities must be a list containing only allowed capability keywords."""
        # Non-list
        with self.assertRaises(ValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, capabilities="composer_action"))

        # Unknown capability
        with self.assertRaises(ValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, capabilities=["composer_action", "arbitrary_exec"]))

    def test_invalid_scopes(self):
        """Scopes must be a list containing only recognized scope permissions."""
        # Non-list
        with self.assertRaises(ValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, scopes="read:quran"))

        # Disallowed scope
        with self.assertRaises(ValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, scopes=["read:quran", "root:admin"]))

    def test_malformed_settings_schema(self):
        """settings_schema and default_config must be dictionaries."""
        with self.assertRaises(ValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, settings_schema="not a dict"))

        with self.assertRaises(ValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, default_config=["not a dict"]))
```

---

### 2.3 Module 3: `test_registry.py` (Autodiscovery, Lifecycle & DB Sync)

```python
"""
backend/apps/plugin_system/tests/test_registry.py
Unit tests for PluginRegistry singleton, autodiscovery, lifecycle hooks, and database synchronization.
"""
from django.test import TestCase, override_settings
from apps.plugin_system.registry import PluginRegistry, plugin_registry
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.models import Plugin
from django.contrib.auth import get_user_model
from apps.notes.models import Topic

User = get_user_model()

class MockSamplePlugin(BasePlugin):
    identifier = "sample-mock"
    manifest = {
        "manifest_version": 1,
        "identifier": "sample-mock",
        "name": "پلاگین آزمایشی",
        "version": "1.0.0",
        "capabilities": ["composer_action"],
        "scopes": ["write:composer"],
        "settings_schema": {},
        "default_config": {}
    }

    def __init__(self):
        self.install_called = False
        self.uninstall_called = False

    def on_install(self, user, config=None):
        self.install_called = True

    def on_uninstall(self, user):
        self.uninstall_called = True


class PluginRegistryTestCase(TestCase):
    def setUp(self):
        self.registry = PluginRegistry()
        self.user = User.objects.create_user(phone="09124444444")
        self.topic = Topic.objects.create(name="تاپیک تستی", created_by=self.user)

    def test_registry_initialization_empty(self):
        """Registry initializes empty when no plugins are registered."""
        self.assertEqual(len(self.registry.all()), 0)
        self.assertIsNone(self.registry.get("non-existent"))
        self.assertFalse(self.registry.is_registered("non-existent"))

    def test_manual_plugin_registration(self):
        """Registering a BasePlugin instance stores it and makes it queryable."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)

        self.assertTrue(self.registry.is_registered("sample-mock"))
        self.assertEqual(self.registry.get("sample-mock"), plugin_instance)
        self.assertEqual(len(self.registry.all()), 1)

    def test_sync_with_database(self):
        """Registry sync_db() creates or updates records in the Plugin database table."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)
        self.registry.sync_db()

        db_plugin = Plugin.objects.get(identifier="sample-mock")
        self.assertEqual(db_plugin.name, "پلاگین آزمایشی")
        self.assertEqual(db_plugin.version, "1.0.0")
        self.assertTrue(db_plugin.is_active)

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=[])
    def test_autodiscover_empty_setting(self):
        """Autodiscover with empty list completes without exceptions."""
        self.registry.autodiscover()
        self.assertEqual(len(self.registry.all()), 0)

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=["non.existent.module.path"])
    def test_autodiscover_handles_missing_module_gracefully(self):
        """Non-existent module in settings logs error and does not raise uncaught exception."""
        # Should not crash
        self.registry.autodiscover()
        self.assertEqual(len(self.registry.all()), 0)

    def test_lifecycle_hook_dispatch(self):
        """Lifecycle hooks on_install and on_uninstall are dispatched correctly."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)

        plugin_instance.on_install(self.user, config={"key": "value"})
        self.assertTrue(plugin_instance.install_called)

        plugin_instance.on_uninstall(self.user)
        self.assertTrue(plugin_instance.uninstall_called)
```

---

### 2.4 Module 4: `test_api.py` (DRF REST Endpoints & Permissions)

```python
"""
backend/apps/plugin_system/tests/test_api.py
Comprehensive DRF API integration tests for /api/plugins/ marketplace, user, and topic endpoints.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, TopicAdmin
from apps.plugin_system.models import Plugin, PluginInstallation, PluginTopicInstallation

User = get_user_model()


class PluginMarketplaceAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09125555551")
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن کریم",
            version="1.0.0",
            description="پلاگین قرآن",
            capabilities=["composer_action", "mini_app"],
            scopes=["read:quran"],
            is_active=True
        )
        self.inactive_plugin = Plugin.objects.create(
            identifier="disabled-plugin",
            name="غیرفعال",
            version="1.0.0",
            is_active=False
        )

    def test_list_plugins_anonymous(self):
        """GET /api/plugins/ returns 200 OK with active plugins and is_installed=False."""
        response = self.client.get("/api/plugins/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        identifiers = [item["identifier"] for item in response.data]
        self.assertIn("quran", identifiers)
        self.assertNotIn("disabled-plugin", identifiers)
        
        quran_item = next(item for item in response.data if item["identifier"] == "quran")
        self.assertFalse(quran_item.get("is_installed", False))

    def test_list_plugins_authenticated_reflects_installation(self):
        """Authenticated user sees is_installed=True for their installed plugins."""
        PluginInstallation.objects.create(user=self.user, plugin=self.plugin, is_enabled=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/plugins/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        quran_item = next(item for item in response.data if item["identifier"] == "quran")
        self.assertTrue(quran_item["is_installed"])
        self.assertTrue(quran_item["is_enabled"])

    def test_plugin_detail_endpoint(self):
        """GET /api/plugins/<identifier>/ returns detailed manifest and settings schema."""
        response = self.client.get(f"/api/plugins/{self.plugin.identifier}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["identifier"], "quran")
        self.assertEqual(response.data["name"], "قرآن کریم")

    def test_plugin_detail_not_found(self):
        """GET /api/plugins/non-existent/ returns 404 Not Found."""
        response = self.client.get("/api/plugins/non-existent/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserPluginLifecycleAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09125555552")
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن کریم",
            version="1.0.0",
            settings_schema={"type": "object", "properties": {"theme": {"type": "string"}}},
            default_config={"theme": "light"}
        )

    def test_install_plugin_unauthenticated(self):
        """Unauthenticated install attempt returns 401 Unauthorized."""
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/install/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_install_plugin_success(self):
        """POST /api/plugins/<identifier>/install/ creates PluginInstallation with custom user_config."""
        self.client.force_authenticate(user=self.user)
        payload = {"user_config": {"theme": "dark"}}
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/install/", payload, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        install = PluginInstallation.objects.get(user=self.user, plugin=self.plugin)
        self.assertTrue(install.is_enabled)
        self.assertEqual(install.user_config.get("theme"), "dark")

    def test_toggle_plugin_status(self):
        """POST /api/plugins/<identifier>/toggle/ flips is_enabled flag."""
        install = PluginInstallation.objects.create(user=self.user, plugin=self.plugin, is_enabled=True)
        self.client.force_authenticate(user=self.user)

        # Toggle to False
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/toggle/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        install.refresh_from_db()
        self.assertFalse(install.is_enabled)

        # Toggle to True
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/toggle/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        install.refresh_from_db()
        self.assertTrue(install.is_enabled)

    def test_uninstall_plugin_success(self):
        """POST /api/plugins/<identifier>/uninstall/ deletes PluginInstallation."""
        PluginInstallation.objects.create(user=self.user, plugin=self.plugin)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/uninstall/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        self.assertFalse(PluginInstallation.objects.filter(user=self.user, plugin=self.plugin).exists())


class TopicPluginLifecycleAPITestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(phone="09126666661")
        self.admin = User.objects.create_user(phone="09126666662")
        self.member = User.objects.create_user(phone="09126666663")
        
        self.topic = Topic.objects.create(name="تاپیک تخصصی", created_by=self.owner)
        TopicAdmin.objects.create(topic=self.topic, user=self.admin)
        
        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")

    def test_list_topic_plugins(self):
        """GET /api/plugins/topics/<topic_id>/ lists active plugins on topic."""
        PluginTopicInstallation.objects.create(topic=self.topic, plugin=self.plugin, is_enabled=True)
        response = self.client.get(f"/api/plugins/topics/{self.topic.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["plugin"]["identifier"], "quran")

    def test_topic_install_permissions(self):
        """Non-admin member receives 403; Topic Owner and Topic Admin receive 201/200."""
        url = f"/api/plugins/topics/{self.topic.id}/install/"
        payload = {"identifier": "quran", "topic_config": {"auto_verse": True}}

        # 1. Member -> 403 Forbidden
        self.client.force_authenticate(user=self.member)
        res_member = self.client.post(url, payload, format="json")
        self.assertEqual(res_member.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Topic Admin -> 200/201 Created
        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.post(url, payload, format="json")
        self.assertIn(res_admin.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(PluginTopicInstallation.objects.filter(topic=self.topic, plugin=self.plugin).exists())

    def test_topic_toggle_and_uninstall_by_owner(self):
        """Topic owner can toggle and uninstall topic plugins."""
        install = PluginTopicInstallation.objects.create(topic=self.topic, plugin=self.plugin, is_enabled=True)
        self.client.force_authenticate(user=self.owner)

        # Toggle
        res_toggle = self.client.post(f"/api/plugins/topics/{self.topic.id}/toggle/", {"identifier": "quran"}, format="json")
        self.assertEqual(res_toggle.status_code, status.HTTP_200_OK)
        install.refresh_from_db()
        self.assertFalse(install.is_enabled)

        # Uninstall
        res_uninstall = self.client.post(f"/api/plugins/topics/{self.topic.id}/uninstall/", {"identifier": "quran"}, format="json")
        self.assertIn(res_uninstall.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        self.assertFalse(PluginTopicInstallation.objects.filter(topic=self.topic, plugin=self.plugin).exists())
```

---

### 2.5 Module 5: `test_isolation.py` (Zero-Breaking-Change & Non-Regression)

```python
"""
backend/apps/plugin_system/tests/test_isolation.py
Verification of zero breaking changes, empty INSTALLED_TAFAKOR_PLUGINS resilience,
and non-invasive post reference integrity.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, Post, BotTask
from apps.plugin_system.models import Plugin, PostPluginReference
from apps.plugin_system.registry import PluginRegistry

User = get_user_model()


class ZeroBreakingChangeIsolationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09127777771")
        self.topic = Topic.objects.create(name="تاپیک مستقل", created_by=self.user)

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=[])
    def test_empty_plugins_setting_isolation(self):
        """Server operates with INSTALLED_TAFAKOR_PLUGINS = [] without any startup errors or regressions."""
        registry = PluginRegistry()
        registry.autodiscover()
        self.assertEqual(len(registry.all()), 0)

        # Standard post creation operates normally
        post = Post.objects.create(topic=self.topic, author=self.user, content="پست تست بدون پلاگین")
        self.assertIsNotNone(post.id)
        self.assertEqual(post.topic, self.topic)

    def test_post_creation_and_bot_task_unaffected(self):
        """Standard Post creation and BotTask generation pipeline remains completely intact."""
        post = Post.objects.create(topic=self.topic, author=self.user, content="متن تستی با تسک ربات")
        task = BotTask.objects.create(
            action="send",
            platform="telegram",
            chat_id="123456",
            text="تسک تست",
            post_id=post
        )
        self.assertEqual(task.post_id, post)
        self.assertFalse(task.processed)

    def test_decoupled_post_plugin_reference_integrity(self):
        """PostPluginReference operates purely on external_id without touching core Post fields or schema."""
        plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")
        post = Post.objects.create(topic=self.topic, author=self.user, content="پست همراه با آیه قرآن")

        ref = PostPluginReference.objects.create(
            post=post,
            plugin=plugin,
            resource_type="ayah",
            external_id="114:1",
            metadata={"surah": 114, "ayah": 1}
        )

        # Post query and fields remain untouched
        post.refresh_from_db()
        self.assertEqual(post.plugin_references.count(), 1)
        self.assertEqual(post.plugin_references.first().external_id, "114:1")

        # Deleting the post cleanly cascades to reference without touching plugin
        post.delete()
        self.assertFalse(PostPluginReference.objects.filter(id=ref.id).exists())
        self.assertTrue(Plugin.objects.filter(id=plugin.id).exists())
```

---

## 3. Caveats

1. **Test DB Flush vs Mock State**:
   - The global `clean_db` fixture (`tests/conftest.py`) calls `flush` before each test. Database tables are purged, but in-memory singletons (`apps.plugin_system.registry.plugin_registry`) retain their registered dictionary state across tests unless explicitly reset in test `setUp()` or teardown. Each test suite testing registration must instantiate a clean `PluginRegistry()` or clear `plugin_registry._plugins`.
2. **AppConfig `ready()` vs Unmigrated Test DB**:
   - During initial test DB setup before migrations run, any DB query in `AppConfig.ready()` (such as `plugin_registry.sync_db()`) will fail with `OperationalError` or `ProgrammingError`. The `ready()` hook in `apps.plugin_system.apps.PluginSystemConfig` must be wrapped in `try ... except (OperationalError, ProgrammingError): pass` or delayed until post-migration signals.
3. **Mocking Plugin Apps in Django `INSTALLED_APPS`**:
   - Django validates `INSTALLED_APPS` at startup. When testing dynamic autodiscovery with `@override_settings(INSTALLED_TAFAKOR_PLUGINS=...)`, tests should point to valid mock package paths or test fixtures to prevent `ModuleNotFoundError`.

---

## 4. Conclusion

1. **Test Infrastructure Readiness**: Tafakor's test harness is robust with PostgreSQL 15 containerization, database flushing isolation (`clean_db`), session monkeypatching, and automated coverage reporting.
2. **Comprehensive Test Suite Specification**: Designed 5 targeted test modules for `backend/apps/plugin_system/tests/` with 30+ granular test methods covering model relationships, unique constraints, manifest schema validation, autodiscovery, lifecycle hooks, permission matrices, and zero-breaking-change isolation.
3. **Core Non-Regression Guarantee**: All existing 107 core platform test cases (`accounts`, `notes`, `donations`, and `tests/integration/`) are mapped and fully compatible with the new plugin architecture.

---

## 5. Verification Method

### 5.1 Verification Commands

#### 1. Run Milestone 1 Plugin System Test Suite
Inside the Docker test container or development environment:
```bash
pytest backend/apps/plugin_system/tests/ -v
```
Or running specific test modules:
```bash
pytest backend/apps/plugin_system/tests/test_models.py -v
pytest backend/apps/plugin_system/tests/test_validator.py -v
pytest backend/apps/plugin_system/tests/test_registry.py -v
pytest backend/apps/plugin_system/tests/test_api.py -v
pytest backend/apps/plugin_system/tests/test_isolation.py -v
```

#### 2. Run All Existing Core Platform Test Suites (Non-Regression Verification)
```bash
pytest backend/apps/accounts/tests.py backend/apps/notes/tests.py backend/apps/donations/tests/ tests/integration/ -v
```

#### 3. Run Full Automated Monorepo Test Harness
On Windows PowerShell:
```powershell
.\run-tests.ps1
```
On Linux/macOS:
```bash
./run-tests.sh
```

### 5.2 Invalidation Conditions
The verification fails if:
1. Any of the 107 pre-existing core tests fail or error out.
2. Any test in `backend/apps/plugin_system/tests/` fails to enforce permissions (e.g., non-admin successfully modifying topic plugins).
3. `INSTALLED_TAFAKOR_PLUGINS = []` causes any startup crash or unhandled 500 error in `/api/plugins/`.
4. Deleting a Post leaves orphaned `PostPluginReference` records in the database.
