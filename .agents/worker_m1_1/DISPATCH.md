## 2026-08-23T20:31:19Z
You are the Worker for Milestone 1 (Generic Plugin System Core).
Working directory: f:\AVA\tafakor\.agents\worker_m1_1

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

You MUST read the following specification files before writing any code:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m1\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_m1_1\handoff.md (Models, Validator, Registry, BasePlugin blueprints)
5. f:\AVA\tafakor\.agents\explorer_m1_2\handoff.md (REST APIs, Serializers, Permissions, URLs, Settings blueprints)
6. f:\AVA\tafakor\.agents\explorer_m1_3\handoff.md (Test Suite blueprints & non-regression requirements)

Your exclusive file write ownership:
- `backend/apps/plugin_system/**`
- `backend/note_platform/settings.py`
- `backend/note_platform/urls.py`

Your implementation tasks:
1. Implement `backend/apps/plugin_system/`:
   - `__init__.py`
   - `apps.py` (`PluginSystemConfig` with safe autodiscovery in `ready()`)
   - `exceptions.py` (`PluginSystemException`, `ManifestValidationError`, `PluginRegistrationError`, `PluginNotFoundError`)
   - `models.py` (`Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference`)
   - `manifest.py` (`PluginManifest` dataclass and parser)
   - `validator.py` (`ManifestValidator` strictly validating `manifest_version == 1`, regex, capabilities, scopes, jsonschema)
   - `base.py` (`BasePlugin` with lifecycle hooks and manifest accessor)
   - `registry.py` (`PluginRegistry` singleton with autodiscovery and migration-safe database sync)
   - `permissions.py` (`IsTopicAdminOrOwner` for topic-level plugin installations)
   - `serializers.py` (`PluginSerializer`, `PluginDetailSerializer`, `PluginInstallationSerializer`, `PluginTopicInstallationSerializer`, `PostPluginReferenceSerializer`, request serializers)
   - `views.py` (`PluginMarketplaceListView`, `PluginDetailView`, `PluginUserInstallView`, `PluginUserUninstallView`, `PluginUserToggleView`, `TopicPluginListView`, `TopicPluginInstallView`, `TopicPluginToggleView`, `TopicPluginUninstallView`, `PostPluginReferenceListCreateView`)
   - `urls.py` (`/api/plugins/` endpoints mapping)
2. Settings & Root URLs integration:
   - In `backend/note_platform/settings.py`: Add `'apps.plugin_system'` to `INSTALLED_APPS` and define `INSTALLED_TAFAKOR_PLUGINS = []` (with dynamic inclusion loop).
   - In `backend/note_platform/urls.py`: Add `path('api/plugins/', include('apps.plugin_system.urls'))`.
3. Create Django Migrations:
   - Run `python manage.py makemigrations plugin_system`
   - Run `python manage.py migrate`
4. Implement complete test suite in `backend/apps/plugin_system/tests/`:
   - `__init__.py`
   - `test_models.py`
   - `test_validator.py`
   - `test_registry.py`
   - `test_api.py`
   - `test_isolation.py`
5. Run test verification commands:
   - Run `python manage.py test apps.plugin_system.tests`
   - Run `python manage.py test apps.accounts apps.notes apps.donations` (Verify 100% pass and 0 regressions on all existing core tests)
6. Write your complete handoff report to `f:\AVA\tafakor\.agents\worker_m1_1\handoff.md`.
7. Send a message to parent reporting completion with exact test outputs.
