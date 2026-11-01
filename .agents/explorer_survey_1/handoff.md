# Handoff Report: Backend Core & Plugin Architecture Investigation (R1)

**Agent**: Explorer 1 (Backend Core & Plugin Architecture Specialist)  
**Date**: 2026-08-23  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_survey_1`  
**Target Subsystem**: R1 - Generic Plugin System Core (`apps/plugin_system`)

---

## 1. Observation

Direct code-level findings across the Tafakor backend codebase:

### 1.1 Django Project Structure & Configuration
- **Settings Location**: `backend/note_platform/settings.py` (204 lines). All Django configuration is consolidated here; there is no split `base.py`/`dev.py`/`prod.py`.
- **PYTHONPATH dynamic initialization**: `backend/note_platform/settings.py:13-14`:
  ```python
  sys.path.insert(0, str(BASE_DIR.parent))
  sys.path.insert(0, str(BASE_DIR))
  ```
- **Current `INSTALLED_APPS`** (`backend/note_platform/settings.py:28-42`):
  ```python
  INSTALLED_APPS = [
      'django.contrib.admin',
      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'django.contrib.staticfiles',

      'rest_framework',
      'rest_framework.authtoken',
      'corsheaders',
      'apps.accounts',
      'apps.notes',
      'apps.donations',
  ]
  ```
- **Authentication & Custom User Model**:
  - `AUTH_USER_MODEL = 'accounts.User'` (`settings.py:69`).
  - `apps.accounts.models.User` uses `phone = models.CharField(max_length=11, unique=True)` as `USERNAME_FIELD` (`apps/accounts/models.py:24-50`).
  - Default primary key is `BigAutoField` (`settings.py:174`).
- **Root URLConf**: `backend/note_platform/urls.py:22-34`:
  ```python
  urlpatterns = [
      path('admin/', admin.site.urls),
      path('api/auth/', include('apps.accounts.urls')),
      path('api/notes/', include('apps.notes.urls')),
      path('api/bot/', include('apps.notes.bot_urls')),
      path('api/v1/donations/', include('apps.donations.urls')),
      path('api/donations/', include('apps.donations.urls')),
      re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
  ]
  ```
- **Database Backend**: PostgreSQL in Docker/production (`DB_HOST` env var present) with SQLite fallback (`backend/db.sqlite3`) for local commands (`settings.py:115-132`).
- **Cache Backend**: Database-backed cache `django.core.cache.backends.db.DatabaseCache` (`table: django_cache`) (`settings.py:164-169`).

### 1.2 Existing Core Models & Relationships
- **`apps.notes.models.Topic`** (`apps/notes/models.py:9-33`):
  - Primary Key: `id` (`BigAutoField`)
  - Fields: `name` (CharField), `image` (FileField), `description` (TextField), `created_by` (FK to User, `SET_NULL`), `telegram_bot_active` (BooleanField), `bale_bot_active` (BooleanField), `telegram_connections` (M2M MessagingTarget), `bale_connections` (M2M MessagingTarget).
- **`apps.notes.models.Post`** (`apps/notes/models.py:60-118`):
  - Primary Key: `id` (`BigAutoField`)
  - Fields: `topic` (FK to Topic, `CASCADE`), `author` (FK to User, `CASCADE`), `content` (TextField Markdown), `media_type` (CharField), `media_file` (FileField), `created_at` (DateTimeField), `updated_at` (DateTimeField), `telegram_message_ids` (JSONField), `bale_message_ids` (JSONField), `content_hash` (CharField 64, SHA256), `published_platforms` (JSONField).
- **`apps.notes.models.BotTask`** (`apps/notes/models.py:146-176`):
  - Fields: `action` (send/edit/delete), `platform` (telegram/bale), `chat_id` (CharField), `text` (TextField), `post_id` (FK to Post, `SET_NULL`), `processed` (BooleanField).
- **`apps.donations.models.DonationCampaign`** (`apps/donations/models.py:9-89`):
  - Primary Key: `id` (`UUIDField`)
  - Fields: `topic` (FK to Topic, `CASCADE`), `creator` (FK to User, `PROTECT`), `post` (OneToOneField to `notes.Post`, `SET_NULL`, `null=True`, `blank=True`), `title`, `description`, `target_amount`, `collected_amount`, `donors_count`, `status`.

### 1.3 Existing Test Suite & Verification Setup
- **`pytest.ini`** (`f:\AVA\tafakor\pytest.ini:1-6`):
  ```ini
  [pytest]
  DJANGO_SETTINGS_MODULE = note_platform.settings
  python_files = test_*.py tests.py
  addopts = --reuse-db -v --cov=backend --cov=bot_runner --cov-report=term-missing --cov-report=html:/app/tests/results/coverage
  norecursedirs = .git node_modules postgres-data venv .pytest_cache frontend/node_modules backend/staticfiles
  ```
- **Test Locations & Count**:
  1. `backend/apps/accounts/tests.py`: 12 unit tests (OTP services, AuthViewSet, OTP dispatcher, Bot register phone/chat).
  2. `backend/apps/notes/tests.py`: 43 unit & API tests (Notes models, Telegram JSON/ZIP imports, File cleanup signals, Topic admins, Phase 2 deduplication, Phase 3 selective delete).
  3. `backend/apps/donations/tests/`: 15 unit tests (`test_models.py` [6], `test_services.py` [3], `test_api.py` [6]).
  4. `tests/integration/`: 37 integration tests (`test_notes_api.py` [12], `test_donations_api.py` [7], `test_bot_api.py` [5], `test_bot_runner.py` [4], `test_bot_handlers.py` [7], `test_telegram_proxy.py` [2]).
  5. `tests/e2e/test_critical_path.py`: 3 Playwright E2E tests (`test_critical_path_login_flow`, `test_donate_navigation_flow`, `test_custom_bot_registration`).
  6. `frontend/src/lib/utils.test.js`: frontend unit tests (Node test runner).
  - Total backend & integration suite has >100 automated test methods running under pytest.
- **Fixtures & DB isolation** (`tests/conftest.py:27-47`):
  - `django_db_setup`: reuses active PostgreSQL database.
  - `clean_db` (`autouse=True`): calls `call_command("flush", interactive=False, reset_sequences=True)` to wipe tables between tests while keeping schema intact.

---

## 2. Logic Chain & Architectural Design

### 2.1 Decoupled Plugin System Architecture (`apps/plugin_system`)

To maintain the **zero-breaking-change architecture** and strict isolation:

```
+-----------------------------------------------------------------------------------+
|                                 CORE PLATFORM                                     |
|                                                                                   |
|  +--------------------+       +--------------------+       +-------------------+  |
|  |    accounts.User   |       |    notes.Topic     |       |    notes.Post     |  |
|  +---------+----------+       +---------+----------+       +---------+---------+  |
|            |                            |                            |            |
+------------|----------------------------|----------------------------|------------+
             |                            |                            |
             |                            |                            |
+------------|----------------------------|----------------------------|------------+
|            v                            v                            v            |
|  +--------------------+       +--------------------+       +-------------------+  |
|  | PluginInstallation |       |PluginTopicInstall. |       |PostPluginReference|  |
|  +---------+----------+       +---------+----------+       +---------+---------+  |
|            |                            |                            |            |
|            +--------------------+       |       +--------------------+            |
|                                 |       |       |                                 |
|                                 v       v       v                                 |
|                              +--------------------+                               |
|                              |   plugin_system.   |                               |
|                              |       Plugin       |                               |
|                              +--------------------+                               |
|                                                                                   |
|                        apps/plugin_system (GENERIC CORE)                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         | Loose coupling via external_id (CharField)
                                         v
+-----------------------------------------------------------------------------------+
|  plugins/quran/ (OFFICIAL PLUGIN)                                                 |
|  +-----------------------------------------------------------------------------+  |
|  | Models: QuranEdition, QuranSurah, QuranAyah, QuranJuz                       |  |
|  | (No foreign key from PostPluginReference to QuranAyah directly)              |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 2.2 Data Models Specification (`apps/plugin_system/models.py`)

#### 1. `Plugin`
Core entity describing an available plugin (system-wide):
```python
import uuid
from django.db import models

class Plugin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=100, unique=True, db_index=True)  # e.g., 'quran'
    name = models.CharField(max_length=255)                                   # e.g., 'قرآن کریم'
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

    def __str__(self):
        return f"{self.name} ({self.identifier} v{self.version})"
```

#### 2. `PluginInstallation` (User-level)
Tracks user activation of marketplace plugins:
```python
class PluginInstallation(models.Model):
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
        ordering = ['-installed_at']
```

#### 3. `PluginTopicInstallation` (Topic-level)
Enables plugin capabilities within a specific Topic:
```python
class PluginTopicInstallation(models.Model):
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
        blank=True
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
        ordering = ['-installed_at']
```

#### 4. `PostPluginReference` (Zero-foreign-key plugin content linking)
```python
class PostPluginReference(models.Model):
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
    resource_type = models.CharField(max_length=50)  # e.g., 'ayah', 'surah'
    external_id = models.CharField(max_length=255, db_index=True)  # e.g., '1:1' or 'surah_114'
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tafakor_post_plugin_references'
        indexes = [
            models.Index(fields=['plugin', 'external_id']),
            models.Index(fields=['post', 'plugin']),
        ]
        ordering = ['created_at']
```

### 2.3 Manifest Specification & Validator (`apps/plugin_system/manifest.py`)

A Tafakor plugin manifest conforms to `manifest_version: 1`:
```json
{
  "manifest_version": 1,
  "identifier": "quran",
  "name": "قرآن کریم",
  "version": "1.0.0",
  "description": "پلاگین رسمی قرآن کریم برای پلتفرم تفکر",
  "author": "Tafakor Team",
  "icon": "BookOpen",
  "entry_point": "plugins.quran.plugin.QuranPlugin",
  "capabilities": [
    "composer_action",
    "mini_app",
    "search_provider",
    "topic_integration"
  ],
  "scopes": [
    "read:quran",
    "write:composer"
  ],
  "frontend": {
    "module": "@/plugins/quran",
    "routes": [
      { "path": "/apps/quran", "name": "QuranReader" }
    ],
    "composer": {
      "icon": "BookOpen",
      "tooltip": "درج آیه قرآن",
      "action": "openQuranModal"
    }
  },
  "settings_schema": {
    "type": "object",
    "properties": {
      "default_edition": { "type": "string", "default": "quran-simple" }
    }
  },
  "default_config": {
    "default_edition": "quran-simple"
  }
}
```

**Manifest Validation Logic (`apps/plugin_system/validator.py`)**:
- Validates `manifest_version == 1`.
- Validates required strings: `identifier`, `name`, `version`.
- Checks `identifier` regex: `^[a-z0-9_-]+$`.
- Validates `capabilities` against allowed list: `['composer_action', 'mini_app', 'search_provider', 'topic_integration', 'bot_action', 'feed_card']`.
- Validates `scopes` against allowed permissions: `['read:content', 'write:composer', 'manage:topic', 'read:quran']`.
- Validates `settings_schema` and `default_config` structure.

### 2.4 Dynamic Plugin Registry (`apps/plugin_system/registry.py`)

```python
import importlib
import json
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

class PluginRegistry:
    def __init__(self):
        self._plugins = {}  # identifier -> BasePlugin instance
        self._manifests = {} # identifier -> manifest dict

    def autodiscover(self):
        """Discovers and registers all plugins declared in INSTALLED_TAFAKOR_PLUGINS."""
        installed_plugin_apps = getattr(settings, 'INSTALLED_TAFAKOR_PLUGINS', [])
        for app_module_path in installed_plugin_apps:
            try:
                self.load_plugin(app_module_path)
            except Exception as e:
                logger.error(f"Failed to load plugin from {app_module_path}: {e}")

    def load_plugin(self, app_module_path: str):
        # 1. Look for manifest (plugin.json or python manifest)
        # 2. Validate manifest via ManifestValidator
        # 3. Instantiate BasePlugin subclass
        # 4. Sync DB record in Plugin model if DB is ready
        # 5. Store in memory registry
        pass

    def get(self, identifier: str):
        return self._plugins.get(identifier)

    def all(self):
        return list(self._plugins.values())

plugin_registry = PluginRegistry()
```

### 2.5 Settings Integration & Isolation Guarantee

In `backend/note_platform/settings.py`:
```python
# ==============================================================================
# Tafakor Plugin System Settings
# ==============================================================================
INSTALLED_TAFAKOR_PLUGINS = [
    'plugins.quran',
]

# Safely append plugin apps to Django INSTALLED_APPS
for _plugin_app in INSTALLED_TAFAKOR_PLUGINS:
    if _plugin_app not in INSTALLED_APPS:
        INSTALLED_APPS.append(_plugin_app)
```

**Non-regression guarantee**:
- If `INSTALLED_TAFAKOR_PLUGINS = []` (or is omitted), `plugin_registry.autodiscover()` iterates over empty list without errors.
- `apps.plugin_system` remains a self-contained Django app in `INSTALLED_APPS` without any hard dependencies on specific plugins.
- None of the core platform endpoints or background tasks (`accounts`, `notes`, `donations`, `bot_runner`) depend on any plugin being installed.

### 2.6 REST API Contract (`/api/plugins/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/plugins/` | AllowAny | Lists marketplace plugins with user installation status |
| `GET` | `/api/plugins/{identifier}/` | AllowAny | Detailed metadata & manifest of a plugin |
| `POST` | `/api/plugins/{identifier}/install/` | IsAuthenticated | Installs plugin for current user (`PluginInstallation`) |
| `POST` | `/api/plugins/{identifier}/uninstall/`| IsAuthenticated | Uninstalls/disables plugin for current user |
| `POST` | `/api/plugins/{identifier}/toggle/` | IsAuthenticated | Toggles `is_enabled` status for user |
| `GET` | `/api/plugins/topics/{topic_id}/` | AllowAny | Lists active plugins for a specific Topic |
| `POST` | `/api/plugins/topics/{topic_id}/install/` | IsTopicOwnerOrAdmin | Installs/enables plugin for Topic (`PluginTopicInstallation`)|
| `POST` | `/api/plugins/topics/{topic_id}/toggle/` | IsTopicOwnerOrAdmin | Toggles plugin `is_enabled` on Topic |
| `POST` | `/api/plugins/topics/{topic_id}/uninstall/`| IsTopicOwnerOrAdmin | Removes plugin from Topic |

---

## 3. Caveats

1. **Database Migration Initialization**: During `python manage.py migrate` or test runners before DB tables are created, `AppConfig.ready()` must wrap `plugin_registry.autodiscover()` in an exception handler (`django.db.utils.ProgrammingError`, `OperationalError`) to prevent crash before migrations finish.
2. **Third-party Plugin Execution**: The marketplace acts strictly as a **feature access and configuration manager**. It does NOT execute dynamic code downloads or arbitrary shell commands at runtime.
3. **No Direct FK to Plugin Tables**: `PostPluginReference` stores `external_id` (CharField) to avoid cascading FK schema lock-in if a plugin is uninstalled or dropped.

---

## 4. Conclusion

1. The existing Tafakor Django backend is well-structured with centralized settings in `note_platform/settings.py` and cleanly isolated apps (`accounts`, `notes`, `donations`).
2. Building `apps/plugin_system` as a standard Django app under `backend/apps/plugin_system` with dynamic discovery of `INSTALLED_TAFAKOR_PLUGINS` provides 100% decoupling with zero risk of regression to existing core features.
3. `PostPluginReference` cleanly bridges post content to plugin resources via `(plugin, external_id, metadata)` without foreign key violations or database schema dependencies on external plugin tables.
4. The test suite setup (`pytest`, `docker-compose.test.yml`, shared test PostgreSQL container with `call_command('flush')`) is solid, and adding dedicated tests under `backend/apps/plugin_system/tests/` will integrate seamlessly.

---

## 5. Verification Method

To independently verify all findings and test integrity:

1. **Verify Backend Codebase & Settings**:
   - Inspect `backend/note_platform/settings.py` lines 28-42 (`INSTALLED_APPS`) and lines 115-132 (`DATABASES`).
   - Inspect `backend/note_platform/urls.py` lines 22-34 (`urlpatterns`).
   - Inspect `backend/apps/notes/models.py` lines 60-118 (`Post` model) and 9-33 (`Topic` model).
2. **Run Existing Core Test Suite**:
   ```powershell
   # Running via PowerShell / Docker Compose test suite
   .\run-tests.ps1
   ```
   Or inside container / local environment:
   ```bash
   pytest -v
   ```
3. **Validate App Isolation**:
   - Set `INSTALLED_TAFAKOR_PLUGINS = []` in settings and execute `python manage.py check`.
   - Verify that all 35+ core unit & integration tests in `apps/accounts/tests.py`, `apps/notes/tests.py`, `apps/donations/tests/`, and `tests/integration/` pass with 0 failures.
