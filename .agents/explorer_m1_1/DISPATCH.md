## 2026-08-23T20:29:08Z

<USER_REQUEST>
You are Explorer 1 for Milestone 1 (Generic Plugin System Core).
Working directory: f:\AVA\tafakor\.agents\explorer_m1_1

You MUST read:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m1\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_survey_1\handoff.md
5. Existing core backend models in `backend/apps/notes/models.py`, `backend/apps/accounts/models.py`, `backend/apps/donations/models.py`.

Your task:
1. Investigate and design exact model definitions for `backend/apps/plugin_system/models.py`:
   - `Plugin` (id: UUID, identifier: str unique, name: str, version: str, description: text, author: str, icon: str, manifest_version: int default 1, capabilities: JSONField, scopes: JSONField, settings_schema: JSONField, default_config: JSONField, is_active: bool, is_core: bool, timestamps).
   - `PluginInstallation` (user FK to AUTH_USER_MODEL, plugin FK to Plugin, is_enabled: bool, user_config: JSONField, unique constraint user+plugin).
   - `PluginTopicInstallation` (topic FK to notes.Topic, plugin FK to Plugin, installed_by FK to AUTH_USER_MODEL null=True, is_enabled: bool, topic_config: JSONField, unique constraint topic+plugin).
   - `PostPluginReference` (post FK to notes.Post, plugin FK to Plugin, resource_type: str, external_id: str indexed, metadata: JSONField, created_at). Note: loose coupling via external_id without FK to plugin-specific tables.
2. Design `BasePlugin` class (`backend/apps/plugin_system/base.py`) and `ManifestValidator` (`backend/apps/plugin_system/validator.py`):
   - Strict validation of `manifest_version == 1`.
   - Capabilities enum/list: `composer_action`, `mini_app`, `search_provider`, `topic_integration`, `bot_action`, `feed_card`.
   - Scopes enum/list: `read:content`, `write:composer`, `manage:topic`, `read:quran`, etc.
   - JSON schema validation for settings_schema and default_config.
3. Design dynamic `PluginRegistry` (`backend/apps/plugin_system/registry.py`) and AppConfig lifecycle hooks (`backend/apps/plugin_system/apps.py`):
   - Safe autodiscovery of plugins in `settings.INSTALLED_TAFAKOR_PLUGINS`.
   - Catch `OperationalError`/`ProgrammingError` during early migration phases so tests and commands run safely.
4. Output your detailed findings and code blueprints to `f:\AVA\tafakor\.agents\explorer_m1_1\handoff.md`.
5. Send a completion message to the parent with a summary and reference to handoff.md.
</USER_REQUEST>
