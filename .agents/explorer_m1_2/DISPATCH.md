## 2026-08-23T20:29:08Z
<USER_REQUEST>
You are Explorer 2 for Milestone 1 (Generic Plugin System Core).
Working directory: f:\AVA\tafakor\.agents\explorer_m1_2

You MUST read:
1. f:\AVA\tafakor\.agents\ORIGINAL_REQUEST.md
2. f:\AVA\tafakor\PROJECT.md
3. f:\AVA\tafakor\.agents\sub_orch_m1\SCOPE.md
4. f:\AVA\tafakor\.agents\explorer_survey_1\handoff.md
5. Existing backend views, permissions, and serializers in `backend/apps/notes/`, `backend/apps/accounts/`, `backend/apps/donations/`.

Your task:
1. Investigate and design REST API endpoints for `/api/plugins/`:
   - `GET /api/plugins/` (AllowAny): List marketplace plugins with `is_installed`, `is_enabled` annotated for the requesting user (if authenticated).
   - `GET /api/plugins/<identifier>/` (AllowAny): Retrieve full plugin details, manifest, and settings_schema.
   - `POST /api/plugins/<identifier>/install/` (IsAuthenticated): Install plugin for user with optional `user_config`.
   - `POST /api/plugins/<identifier>/uninstall/` (IsAuthenticated): Uninstall plugin for user.
   - `POST /api/plugins/<identifier>/toggle/` (IsAuthenticated): Toggle `is_enabled` on user installation.
   - `GET /api/plugins/topics/<topic_id>/` (AllowAny / IsTopicMember): List active topic plugins.
   - `POST /api/plugins/topics/<topic_id>/install/` (IsTopicAdminOrOwner): Install/enable plugin on a Topic.
   - `POST /api/plugins/topics/<topic_id>/toggle/` (IsTopicAdminOrOwner): Toggle `is_enabled` on Topic.
   - `POST /api/plugins/topics/<topic_id>/uninstall/` (IsTopicAdminOrOwner): Uninstall plugin from Topic.
2. Design Serializers (`backend/apps/plugin_system/serializers.py`):
   - `PluginSerializer`, `PluginDetailSerializer`, `PluginInstallationSerializer`, `PluginTopicInstallationSerializer`, `PostPluginReferenceSerializer`.
3. Design Permissions (`backend/apps/plugin_system/permissions.py`):
   - `IsTopicAdminOrOwner`: checks if requesting user is topic creator, or in topic admins/moderators (check `apps.notes.models.Topic` and related permission conventions).
4. Design URL Routing (`backend/apps/plugin_system/urls.py`) and root URL routing integration in `backend/note_platform/urls.py`.
5. Design settings integration in `backend/note_platform/settings.py` (`INSTALLED_APPS` and `INSTALLED_TAFAKOR_PLUGINS = []`).
6. Output your detailed findings and code blueprints to `f:\AVA\tafakor\.agents\explorer_m1_2\handoff.md`.
7. Send a completion message to the parent with a summary and reference to handoff.md.
</USER_REQUEST>
