# Scope: Milestone 1 — Generic Plugin System Core

## Architecture
Generic, decoupled backend plugin system for Tafakor platform residing in `backend/apps/plugin_system/`.

```
backend/
├── note_platform/
│   ├── settings.py           # Includes 'apps.plugin_system' in INSTALLED_APPS & INSTALLED_TAFAKOR_PLUGINS = []
│   └── urls.py               # Routes /api/plugins/ -> apps.plugin_system.urls
└── apps/
    └── plugin_system/
        ├── __init__.py
        ├── apps.py           # PluginSystemConfig with autodiscover hook
        ├── exceptions.py     # PluginSystemException, ManifestValidationError, PluginRegistrationError
        ├── models.py         # Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference
        ├── base.py           # BasePlugin class for plugin authoring
        ├── manifest.py       # PluginManifest dataclass / parser
        ├── validator.py      # ManifestValidator (manifest_version: 1, capabilities, scopes, schema)
        ├── registry.py       # PluginRegistry singleton with autodiscovery & lifecycle
        ├── serializers.py    # DRF serializers for plugins, installations, topic installations
        ├── permissions.py    # IsTopicAdminOrOwner permission classes
        ├── views.py          # ViewSets / APIViews for marketplace, user install, topic install
        ├── urls.py           # REST endpoints mapping
        └── tests/            # Comprehensive test suite (111 tests passing)
            ├── __init__.py
            ├── test_models.py
            ├── test_validator.py
            ├── test_registry.py
            ├── test_api.py
            ├── test_isolation.py
            ├── test_adversarial_api.py
            └── test_challenger_adversarial.py
```

## Feature Inventory (Milestone 1)
| # | Feature | Description | Milestone | Source |
|---|---|---|---|---|
| 1 | Core Plugin Models | `Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference` | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Manifest Validator | Schema validation for `manifest_version: 1`, scopes, capabilities, settings schema | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Dynamic Plugin Registry | `registry.py` autodiscovering and managing installed plugins lifecycle | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Settings Isolation | `INSTALLED_TAFAKOR_PLUGINS` setting with safe empty fallback | M1 | ORIGINAL_REQUEST §R1 |
| 5 | Plugin Management APIs | REST endpoints `/api/plugins/` for marketplace listing, user & topic install/toggle | M1 | ORIGINAL_REQUEST §R1 |

## Milestones & Status
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Generic Plugin System Core | Backend `apps/plugin_system` models, manifest validator, registry, settings, APIs & tests | none | DONE |

## Interface Contracts
### 1. Backend Core Plugin System ↔ Plugins
- **Manifest**: Plugins provide `manifest.json` (or dict) with:
  - `manifest_version`: 1
  - `identifier`: regex `^[a-z0-9_-]+$`
  - `name`: string
  - `version`: semver string
  - `capabilities`: list of `['composer_action', 'mini_app', 'search_provider', 'topic_integration', 'bot_action', 'feed_card']`
  - `scopes`: list of `['read:content', 'write:composer', 'manage:topic', 'read:quran', 'write:bot']`
  - `settings_schema`: JSON schema dict
  - `default_config`: dict
- **Base Plugin**: `BasePlugin` in `apps.plugin_system.base` provides lifecycle hooks (`on_install`, `on_uninstall`, `on_enable`, `on_disable`, `get_manifest`, `validate_config`).
- **Post Reference**: `PostPluginReference` links `Post` to `Plugin` via `(post, plugin, resource_type, external_id, metadata)` without foreign key to plugin-specific tables.

### 2. REST API Specification (`/api/plugins/`)
- `GET /api/plugins/` (AllowAny): List all active marketplace plugins with user installation status if authenticated.
- `GET /api/plugins/<identifier>/` (AllowAny): Retrieve detailed plugin manifest & settings schema.
- `POST /api/plugins/<identifier>/install/` (IsAuthenticated): Install plugin for current user with optional `user_config`.
- `POST /api/plugins/<identifier>/uninstall/` (IsAuthenticated): Remove plugin installation for current user.
- `POST /api/plugins/<identifier>/toggle/` (IsAuthenticated): Toggle `is_enabled` status for current user.
- `GET /api/plugins/topics/<topic_id>/` (AllowAny / IsTopicMember): List active plugins for topic.
- `POST /api/plugins/topics/<topic_id>/install/` (IsTopicAdminOrOwner): Install/enable plugin for topic with optional `topic_config`.
- `POST /api/plugins/topics/<topic_id>/toggle/` (IsTopicAdminOrOwner): Toggle `is_enabled` on topic.
- `POST /api/plugins/topics/<topic_id>/uninstall/` (IsTopicAdminOrOwner): Uninstall plugin from topic.
- `GET /api/plugins/posts/<post_id>/references/` (AllowAny): List post plugin references.
- `POST /api/plugins/posts/<post_id>/references/` (IsAuthenticated, Author/Admin): Attach plugin reference to post.
