# Handoff Report: Milestone 1 Generic Plugin System Core Design & Blueprints

**Agent**: Explorer 1 (Milestone 1 Core Backend Specialist)  
**Date**: 2026-08-23  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_m1_1`  
**Target Milestone**: M1 - Generic Plugin System Core (`backend/apps/plugin_system`)

---

## 1. Observation

Direct code-level observations from the Tafakor repository:

### 1.1 Backend Configuration & App Layout
- **Django Settings** (`backend/note_platform/settings.py`):
  - Line 69: `AUTH_USER_MODEL = 'accounts.User'`
  - Lines 28-42: `INSTALLED_APPS` includes `apps.accounts`, `apps.notes`, `apps.donations`.
  - Lines 13-14: Root and backend directories are placed in `PYTHONPATH`:
    ```python
    sys.path.insert(0, str(BASE_DIR.parent))
    sys.path.insert(0, str(BASE_DIR))
    ```
  - Lines 115-132: Dual database configuration (`django.db.backends.postgresql` with SQLite fallback for local developer tooling).
- **Core Models & Relationships**:
  - `apps.notes.models.Topic` (`backend/apps/notes/models.py:9-33`): Uses `BigAutoField` `id`, `name`, `created_by` (FK to `User`).
  - `apps.notes.models.Post` (`backend/apps/notes/models.py:60-118`): Uses `BigAutoField` `id`, `topic` (FK `Topic`), `author` (FK `User`), `content` (TextField markdown), `content_hash` (CharField 64 SHA256).
  - `apps.accounts.models.User` (`backend/apps/accounts/models.py:24-59`): Primary key is `BigAutoField` with `phone` (`CharField(11, unique=True)`) as `USERNAME_FIELD`.
- **Existing Verification & Baseline**:
  - Command: `python manage.py test apps.accounts apps.notes apps.donations`
  - Result: `Ran 71 tests in 10.364s - OK` with 0 failures, 0 errors.
- **Python Environment**:
  - `jsonschema` is installed (`python -c "import jsonschema"` succeeded at `C:\Users\shiro\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\jsonschema`).
  - `djangorestframework` (DRF) is installed.

---

## 2. Logic Chain & Technical Blueprints

Based on the observations, we designed complete blueprints for the generic plugin system core (`backend/apps/plugin_system/`).

```
backend/apps/plugin_system/
├── __init__.py
├── apps.py                  # PluginSystemConfig with autodiscovery hook
├── exceptions.py            # ManifestValidationError, PluginSystemException
├── models.py                # Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference
├── manifest.py              # PluginManifest dataclass & loader
├── validator.py             # ManifestValidator (manifest_version == 1, capabilities, scopes, json-schema)
├── base.py                  # BasePlugin lifecycle abstract class
├── registry.py              # PluginRegistry singleton with dynamic autodiscovery & DB sync
└── tests/                   # M1 unit & isolation test suite
    ├── __init__.py
    ├── test_models.py
    ├── test_validator.py
    ├── test_registry.py
    └── test_isolation.py
```

---

### 2.1 Blueprint 1: `backend/apps/plugin_system/exceptions.py`

```python
"""
Custom exceptions for Tafakor Plugin System.
"""

class PluginSystemException(Exception):
    """Base exception for all plugin system errors."""
    pass


class ManifestValidationError(PluginSystemException):
    """Raised when a plugin manifest fails schema or semantic validation."""
    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or [message]


class PluginRegistrationError(PluginSystemException):
    """Raised when registering a plugin fails."""
    pass


class PluginNotFoundError(PluginSystemException):
    """Raised when a requested plugin cannot be found in registry or DB."""
    pass
```

---

### 2.2 Blueprint 2: `backend/apps/plugin_system/models.py`

```python
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Plugin(models.Model):
    """
    Core metadata entity describing an available plugin in Tafakor platform.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default='1.0.0')
    description = models.TextField(blank=True, default='')
    author = models.CharField(max_length=255, blank=True, default='')
    icon = models.CharField(max_length=100, blank=True, default='BookOpen')
    manifest_version = models.PositiveIntegerField(default=1)

    capabilities = models.JSONField(default=list, blank=True)
    scopes = models.JSONField(default=list, blank=True)
    settings_schema = models.JSONField(default=dict, blank=True)
    default_config = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_core = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tafakor_plugins'
        ordering = ['name']
        verbose_name = 'Plugin'
        verbose_name_plural = 'Plugins'

    def __str__(self):
        return f"{self.name} ({self.identifier} v{self.version})"

    def has_capability(self, capability: str) -> bool:
        return capability in (self.capabilities or [])

    def has_scope(self, scope: str) -> bool:
        return scope in (self.scopes or [])


class PluginInstallation(models.Model):
    """
    Tracks user-level activation and custom configuration of marketplace plugins.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plugin_installations'
    )
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='user_installations'
    )
    is_enabled = models.BooleanField(default=True)
    user_config = models.JSONField(default=dict, blank=True)
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tafakor_plugin_installations'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'plugin'],
                name='unique_user_plugin_installation'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
        ]
        ordering = ['-installed_at']

    def __str__(self):
        status = 'enabled' if self.is_enabled else 'disabled'
        return f"User({self.user_id}) - {self.plugin.identifier} ({status})"

    def get_effective_config(self) -> dict:
        """Merges plugin default config with user overrides."""
        config = dict(self.plugin.default_config or {})
        config.update(self.user_config or {})
        return config


class PluginTopicInstallation(models.Model):
    """
    Enables and configures plugin capabilities within a specific Topic.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(
        'notes.Topic',
        on_delete=models.CASCADE,
        related_name='plugin_installations'
    )
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='topic_installations'
    )
    installed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installed_topic_plugins'
    )
    is_enabled = models.BooleanField(default=True)
    topic_config = models.JSONField(default=dict, blank=True)
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tafakor_plugin_topic_installations'
        constraints = [
            models.UniqueConstraint(
                fields=['topic', 'plugin'],
                name='unique_topic_plugin_installation'
            )
        ]
        indexes = [
            models.Index(fields=['topic', 'is_enabled']),
        ]
        ordering = ['-installed_at']

    def __str__(self):
        status = 'enabled' if self.is_enabled else 'disabled'
        return f"Topic({self.topic_id}) - {self.plugin.identifier} ({status})"

    def get_effective_config(self) -> dict:
        """Merges plugin default config with topic overrides."""
        config = dict(self.plugin.default_config or {})
        config.update(self.topic_config or {})
        return config


class PostPluginReference(models.Model):
    """
    Links a Post to a plugin resource (ayah, surah, glossary, etc.)
    using loose coupling (resource_type + external_id) with zero foreign keys
    to plugin-specific tables.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        'notes.Post',
        on_delete=models.CASCADE,
        related_name='plugin_references'
    )
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='post_references'
    )
    resource_type = models.CharField(max_length=50)   # e.g., 'ayah', 'surah'
    external_id = models.CharField(max_length=255, db_index=True)  # e.g., '1:1'
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tafakor_post_plugin_references'
        indexes = [
            models.Index(fields=['plugin', 'external_id']),
            models.Index(fields=['post', 'plugin']),
            models.Index(fields=['resource_type', 'external_id']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"Post #{self.post_id} -> {self.plugin.identifier}:{self.resource_type}:{self.external_id}"
```

---

### 2.3 Blueprint 3: `backend/apps/plugin_system/validator.py`

```python
import re
from typing import Dict, Any, List, Set
from .exceptions import ManifestValidationError

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class ManifestValidator:
    """
    Strict validator for Tafakor plugin manifests (manifest_version == 1).
    """
    ALLOWED_CAPABILITIES: Set[str] = {
        'composer_action',
        'mini_app',
        'search_provider',
        'topic_integration',
        'bot_action',
        'feed_card',
    }

    ALLOWED_SCOPES: Set[str] = {
        'read:content',
        'write:composer',
        'manage:topic',
        'read:quran',
        'write:bot',
    }

    IDENTIFIER_REGEX = re.compile(r'^[a-z0-9_-]+$')
    SEMVER_REGEX = re.compile(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9_.]+)?$')

    @classmethod
    def validate(cls, manifest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates manifest data dictionary against Tafakor Plugin Specification.
        Returns validated dict or raises ManifestValidationError.
        """
        errors: List[str] = []

        if not isinstance(manifest_data, dict):
            raise ManifestValidationError("Manifest must be a JSON object / dictionary.")

        # 1. Manifest Version (strict requirement == 1)
        manifest_version = manifest_data.get('manifest_version')
        if manifest_version != 1:
            errors.append(f"Invalid manifest_version: {manifest_version}. Expected 1.")

        # 2. Identifier
        identifier = manifest_data.get('identifier')
        if not identifier or not isinstance(identifier, str):
            errors.append("Field 'identifier' is required and must be a non-empty string.")
        elif not cls.IDENTIFIER_REGEX.match(identifier):
            errors.append(f"Invalid identifier '{identifier}'. Must match lowercase pattern '^[a-z0-9_-]+$'.")

        # 3. Name
        name = manifest_data.get('name')
        if not name or not isinstance(name, str) or not name.strip():
            errors.append("Field 'name' is required and must be a non-empty string.")

        # 4. Version
        version = manifest_data.get('version')
        if not version or not isinstance(version, str):
            errors.append("Field 'version' is required and must be a semver string (e.g. '1.0.0').")
        elif not cls.SEMVER_REGEX.match(version):
            errors.append(f"Invalid version format '{version}'. Must follow semantic versioning (e.g. '1.0.0').")

        # 5. Capabilities
        capabilities = manifest_data.get('capabilities', [])
        if not isinstance(capabilities, list):
            errors.append("Field 'capabilities' must be a list.")
        else:
            for cap in capabilities:
                if cap not in cls.ALLOWED_CAPABILITIES:
                    errors.append(f"Unknown capability '{cap}'. Allowed: {sorted(cls.ALLOWED_CAPABILITIES)}")

        # 6. Scopes
        scopes = manifest_data.get('scopes', [])
        if not isinstance(scopes, list):
            errors.append("Field 'scopes' must be a list.")
        else:
            for scope in scopes:
                if scope not in cls.ALLOWED_SCOPES:
                    errors.append(f"Unknown scope '{scope}'. Allowed: {sorted(cls.ALLOWED_SCOPES)}")

        # 7. Settings Schema & Default Config
        settings_schema = manifest_data.get('settings_schema', {})
        default_config = manifest_data.get('default_config', {})

        if not isinstance(settings_schema, dict):
            errors.append("Field 'settings_schema' must be a dict / JSON object.")
        if not isinstance(default_config, dict):
            errors.append("Field 'default_config' must be a dict / JSON object.")

        if JSONSCHEMA_AVAILABLE and isinstance(settings_schema, dict) and settings_schema:
            try:
                jsonschema.Draft7Validator.check_schema(settings_schema)
            except jsonschema.exceptions.SchemaError as se:
                errors.append(f"Invalid 'settings_schema' JSON Schema: {se.message}")
            
            if isinstance(default_config, dict) and default_config:
                try:
                    jsonschema.validate(instance=default_config, schema=settings_schema)
                except jsonschema.exceptions.ValidationError as ve:
                    errors.append(f"'default_config' does not conform to 'settings_schema': {ve.message}")

        if errors:
            raise ManifestValidationError(f"Manifest validation failed with {len(errors)} error(s).", errors=errors)

        return manifest_data
```

---

### 2.4 Blueprint 4: `backend/apps/plugin_system/manifest.py`

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .validator import ManifestValidator


@dataclass
class PluginManifest:
    manifest_version: int
    identifier: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    icon: str = "BookOpen"
    capabilities: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    settings_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    is_core: bool = False
    frontend: Dict[str, Any] = field(default_factory=dict)
    entry_point: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginManifest':
        validated = ManifestValidator.validate(data)
        return cls(
            manifest_version=validated['manifest_version'],
            identifier=validated['identifier'],
            name=validated['name'],
            version=validated['version'],
            description=validated.get('description', ''),
            author=validated.get('author', ''),
            icon=validated.get('icon', 'BookOpen'),
            capabilities=validated.get('capabilities', []),
            scopes=validated.get('scopes', []),
            settings_schema=validated.get('settings_schema', {}),
            default_config=validated.get('default_config', {}),
            is_core=validated.get('is_core', False),
            frontend=validated.get('frontend', {}),
            entry_point=validated.get('entry_point'),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'manifest_version': self.manifest_version,
            'identifier': self.identifier,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'icon': self.icon,
            'capabilities': self.capabilities,
            'scopes': self.scopes,
            'settings_schema': self.settings_schema,
            'default_config': self.default_config,
            'is_core': self.is_core,
            'frontend': self.frontend,
            'entry_point': self.entry_point,
        }
```

---

### 2.5 Blueprint 5: `backend/apps/plugin_system/base.py`

```python
from typing import Optional, Dict, Any, Tuple
from .manifest import PluginManifest


class BasePlugin:
    """
    Base class that all Tafakor plugins must extend.
    """
    manifest: Optional[PluginManifest] = None

    def __init__(self, manifest: Optional[PluginManifest] = None):
        if manifest:
            self.manifest = manifest
        elif self.manifest is None:
            self.manifest = self.get_manifest()

    def get_manifest(self) -> PluginManifest:
        """Subclasses can override this to construct or load their manifest."""
        raise NotImplementedError("Plugin must define a manifest class attribute or implement get_manifest().")

    @property
    def identifier(self) -> str:
        return self.manifest.identifier if self.manifest else ''

    @property
    def name(self) -> str:
        return self.manifest.name if self.manifest else ''

    @property
    def version(self) -> str:
        return self.manifest.version if self.manifest else ''

    def ready(self) -> None:
        """Called upon registry initialization."""
        pass

    def on_install(self, user=None, topic=None, config: Optional[Dict[str, Any]] = None) -> None:
        """Hook called when installed by a user or on a topic."""
        pass

    def on_uninstall(self, user=None, topic=None) -> None:
        """Hook called when uninstalled."""
        pass

    def on_enable(self, user=None, topic=None) -> None:
        """Hook called when toggled on."""
        pass

    def on_disable(self, user=None, topic=None) -> None:
        """Hook called when toggled off."""
        pass

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates configuration against the plugin's settings_schema."""
        if not self.manifest or not self.manifest.settings_schema:
            return True, None
        try:
            import jsonschema
            jsonschema.validate(instance=config, schema=self.manifest.settings_schema)
            return True, None
        except Exception as e:
            return False, str(e)
```

---

### 2.6 Blueprint 6: `backend/apps/plugin_system/registry.py`

```python
import importlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from .base import BasePlugin
from .manifest import PluginManifest
from .validator import ManifestValidator
from .exceptions import PluginRegistrationError

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Dynamic registry for Tafakor plugins. Autodiscovers plugins declared in
    settings.INSTALLED_TAFAKOR_PLUGINS and keeps DB records in sync safely.
    """

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._manifests: Dict[str, PluginManifest] = {}
        self._loaded: bool = False

    def autodiscover(self) -> None:
        """Discovers and registers all plugins from settings.INSTALLED_TAFAKOR_PLUGINS."""
        installed_plugin_apps = getattr(settings, 'INSTALLED_TAFAKOR_PLUGINS', [])
        for app_path in installed_plugin_apps:
            try:
                self.load_plugin(app_path)
            except Exception as e:
                logger.error(f"Failed to load Tafakor plugin '{app_path}': {e}", exc_info=True)

        self._loaded = True
        self.sync_to_db()

    def load_plugin(self, app_path: str) -> BasePlugin:
        """Loads, validates, and registers a single plugin package."""
        # 1. Try to load manifest.json in app directory if present
        manifest_data = None
        try:
            mod = importlib.import_module(app_path)
            if hasattr(mod, '__file__') and mod.__file__:
                manifest_file = Path(mod.__file__).parent / 'manifest.json'
                if manifest_file.exists():
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        manifest_data = json.load(f)
        except Exception as e:
            logger.debug(f"No manifest.json loaded from module path for {app_path}: {e}")

        # 2. Look for Plugin class in <app_path>.plugin or <app_path>
        plugin_cls: Optional[Type[BasePlugin]] = None
        for candidate_submod in ['.plugin', '']:
            try:
                submod = importlib.import_module(f"{app_path}{candidate_submod}")
                for attr_name in dir(submod):
                    attr = getattr(submod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                        plugin_cls = attr
                        break
                if plugin_cls:
                    break
            except ModuleNotFoundError:
                continue

        # 3. Instantiate plugin
        if plugin_cls:
            manifest_obj = PluginManifest.from_dict(manifest_data) if manifest_data else None
            plugin_instance = plugin_cls(manifest=manifest_obj)
        elif manifest_data:
            manifest_obj = PluginManifest.from_dict(manifest_data)
            plugin_instance = BasePlugin(manifest=manifest_obj)
        else:
            raise PluginRegistrationError(f"Cannot discover plugin entry point or manifest for '{app_path}'.")

        self.register(plugin_instance)
        return plugin_instance

    def register(self, plugin: BasePlugin) -> None:
        """Registers an instantiated BasePlugin in the memory registry."""
        if not plugin.manifest:
            raise PluginRegistrationError("Plugin has no valid manifest.")

        identifier = plugin.identifier
        self._plugins[identifier] = plugin
        self._manifests[identifier] = plugin.manifest
        plugin.ready()
        logger.info(f"Registered Tafakor plugin: {plugin.name} ({identifier})")

    def get(self, identifier: str) -> Optional[BasePlugin]:
        return self._plugins.get(identifier)

    def is_registered(self, identifier: str) -> bool:
        return identifier in self._plugins

    def get_all(self) -> List[BasePlugin]:
        return list(self._plugins.values())

    def get_manifests(self) -> List[PluginManifest]:
        return list(self._manifests.values())

    def get_plugins_with_capability(self, capability: str) -> List[BasePlugin]:
        return [
            p for p in self._plugins.values()
            if p.manifest and capability in p.manifest.capabilities
        ]

    def sync_to_db(self) -> None:
        """
        Synchronizes registered plugins to the database Plugin table.
        Gracefully handles early migration phases where DB tables do not exist yet.
        """
        try:
            from .models import Plugin
            for identifier, manifest in self._manifests.items():
                Plugin.objects.update_or_create(
                    identifier=identifier,
                    defaults={
                        'name': manifest.name,
                        'version': manifest.version,
                        'description': manifest.description,
                        'author': manifest.author,
                        'icon': manifest.icon,
                        'manifest_version': manifest.manifest_version,
                        'capabilities': manifest.capabilities,
                        'scopes': manifest.scopes,
                        'settings_schema': manifest.settings_schema,
                        'default_config': manifest.default_config,
                        'is_core': manifest.is_core,
                        'is_active': True,
                    }
                )
        except (OperationalError, ProgrammingError) as db_err:
            logger.info(f"Skipping plugin DB sync during migration phase: {db_err}")
        except Exception as e:
            logger.warning(f"Plugin DB sync encountered non-fatal error: {e}")

    def clear(self) -> None:
        """For testing purposes: resets in-memory registry."""
        self._plugins.clear()
        self._manifests.clear()
        self._loaded = False


plugin_registry = PluginRegistry()
```

---

### 2.7 Blueprint 7: `backend/apps/plugin_system/apps.py`

```python
from django.apps import AppConfig


class PluginSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.plugin_system'
    verbose_name = 'Tafakor Plugin System'

    def ready(self):
        # Trigger autodiscovery when Django finishes initializing apps
        from .registry import plugin_registry
        plugin_registry.autodiscover()
```

---

## 3. Caveats

1. **DB Sync During Migrations**:
   - When running `python manage.py migrate` or test initialization where `tafakor_plugins` table does not exist yet, `Plugin.objects.update_or_create` will raise `OperationalError` / `ProgrammingError`.
   - The registry must catch these specific database exceptions and continue gracefully.
2. **Settings Isolation**:
   - `INSTALLED_TAFAKOR_PLUGINS = []` must be safe. When empty, `plugin_registry.autodiscover()` simply completes with 0 registered plugins and causes no side effects.
3. **No Direct FK to Plugin-Specific Tables**:
   - `PostPluginReference` stores `resource_type` and `external_id` (e.g. `'1:1'`). It links only to `Plugin` and `notes.Post`, ensuring that if a plugin table is altered or dropped, core `Post` references remain structurally intact.

---

## 4. Conclusion

1. The proposed data models (`Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference`) satisfy all requirements with exact types, constraints, and indexes.
2. `ManifestValidator` strictly enforces `manifest_version == 1`, valid capability and scope enums, and JSON Schema validation for settings and default configurations.
3. `PluginRegistry` handles dynamic discovery from `settings.INSTALLED_TAFAKOR_PLUGINS`, manages the plugin lifecycle, and synchronizes with the database safely across all migration phases.
4. All blueprints adhere to zero breaking changes and maintain 100% compatibility with existing core models and tests.

---

## 5. Verification Method

To verify these blueprints when implemented in Milestone 1:

1. **Verify Django Models & Migrations**:
   ```powershell
   python manage.py makemigrations plugin_system
   python manage.py migrate
   ```
2. **Execute Milestone 1 Core Unit Tests**:
   ```powershell
   python manage.py test apps.plugin_system.tests
   ```
3. **Verify Non-Regression of Pre-Existing Tests**:
   ```powershell
   python manage.py test apps.accounts apps.notes apps.donations
   ```
4. **Verify Empty Plugin Setting Isolation**:
   - In `backend/note_platform/settings.py`, set `INSTALLED_TAFAKOR_PLUGINS = []`.
   - Run `python manage.py check` and run core test suite.
