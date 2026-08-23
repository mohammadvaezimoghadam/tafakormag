## 2026-08-23T20:25:09Z
You are Explorer 1 (Backend Core & Plugin Architecture Specialist).
Your working directory is f:\AVA\tafakor\.agents\explorer_survey_1.
You must read f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md first.

Your task is to thoroughly survey the existing backend codebase and investigate requirements for R1 (Generic Plugin System Core):
1. Investigate the existing Django project structure, apps, settings (where settings are defined, base/dev/prod configs, how INSTALLED_APPS are configured).
2. Investigate existing models related to Topics, Posts, Bot Tasks, Auth/Users, and see where `PostPluginReference` should integrate without foreign key violations.
3. Investigate the existing test suite (where the 35 existing core tests are, how pytest or manage.py test runs, what dependencies/fixtures they use).
4. Analyze architectural design for `apps/plugin_system`:
   - Models: `Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference`.
   - Manifest specification and validator (`manifest_version: 1`, required fields, permission scopes, capabilities).
   - Dynamic plugin registry (`registry.py`) and lifecycle management.
   - Settings integration: `INSTALLED_TAFAKOR_PLUGINS`, ensuring an empty or absent list does not crash anything.
   - DRF ViewSets/endpoints for `/api/plugins/` (marketplace listing, user/topic installation, enable/disable).
5. Write your complete, detailed findings with concrete file paths, schema designs, API contracts, and non-regression considerations into f:\AVA\tafakor\.agents\explorer_survey_1\handoff.md.
6. When done, send a message to parent reporting completion and referencing the handoff report path.
