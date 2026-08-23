# Handoff Report: REST API Endpoints, Serializers, Permissions & Settings Integration (M1)

**Agent**: Explorer 2 (REST API, Serializers & Architecture Specialist)  
**Date**: 2026-08-23  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_m1_2`  
**Target Subsystem**: Milestone 1 - Generic Plugin System Core (`backend/apps/plugin_system/`)

---

## 1. Observation

Direct inspection of existing codebase structures, models, and architectural patterns:

### 1.1 Existing Models & Relationships
1. **`apps.notes.models.Topic`** (`backend/apps/notes/models.py:9-33`):
   - Primary key: `id` (`BigAutoField`).
   - Fields: `name`, `image`, `description`, `created_by` (FK to `accounts.User`), `created_at`, `telegram_bot_active`, `bale_bot_active`, `telegram_connections`, `bale_connections`.
2. **`apps.notes.models.TopicAdmin`** (`backend/apps/notes/models.py:202-229`):
   - Fields: `id` (`UUIDField`), `topic` (FK to `Topic`, `related_name='admins'`), `user` (FK to `User`, `related_name='administered_topics'`), `promoted_by`, `custom_title`, `created_at`.
   - Unique together: `('topic', 'user')`.
3. **`apps.notes.models.Post`** (`backend/apps/notes/models.py:60-118`):
   - Primary key: `id` (`BigAutoField`).
   - Fields: `topic` (FK to `Topic`), `author` (FK to `User`), `content` (Markdown), `media_type`, `media_file`, `created_at`, `content_hash`, `published_platforms`.
4. **`apps.accounts.models.User`** (`backend/apps/accounts/models.py:24-50`):
   - `USERNAME_FIELD = 'phone'` (11 chars).
   - Fields: `id`, `phone`, `first_name`, `last_name`, `profile_image`, `is_active`, `is_staff`, `is_superuser`.

### 1.2 Existing Permissions Pattern
- **`apps.notes.permissions.IsTopicOwnerOrAdmin`** (`backend/apps/notes/permissions.py:5-39`):
  - SAFE methods (`GET`, `HEAD`, `OPTIONS`) return `True`.
  - Superuser returns `True`.
  - Owner check: `topic.created_by == request.user`.
  - Admin check: `topic.admins.filter(user=request.user).exists()`.

### 1.3 Existing Settings & Root URLs
- **`backend/note_platform/settings.py`**:
  - `INSTALLED_APPS` (lines 28-42) lists standard Django apps plus `'apps.accounts'`, `'apps.notes'`, `'apps.donations'`.
  - `REST_FRAMEWORK` (lines 47-54) uses `TokenAuthentication` and `DEFAULT_PERMISSION_CLASSES = ['rest_framework.permissions.IsAuthenticated']`.
- **`backend/note_platform/urls.py`** (lines 22-34):
  - Roots: `admin/`, `api/auth/`, `api/notes/`, `api/bot/`, `api/v1/donations/`, `api/donations/`, and `media/`.

---

## 2. Logic Chain & Technical Blueprints

### 2.1 REST API Endpoint Specification

The `/api/plugins/` namespace provides complete marketplace and lifecycle management across User and Topic contexts.

| HTTP Method | Path | Auth / Permission | Request Body | Response Status & Body | Description |
|---|---|---|---|---|---|
| `GET` | `/api/plugins/` | `AllowAny` | None | `200 OK`<br>`[PluginSerializer]` | List marketplace plugins. For authenticated users, annotates `is_installed`, `is_enabled`, `user_config`. For anonymous users, returns `is_installed=False`, `is_enabled=False`. Supports `?search=` and `?capability=` query parameters. |
| `GET` | `/api/plugins/<identifier>/` | `AllowAny` | None | `200 OK`<br>`PluginDetailSerializer` | Detailed manifest, `settings_schema`, `default_config`, and requesting user's installation status. Returns `404` if not found or inactive. |
| `POST` | `/api/plugins/<identifier>/install/` | `IsAuthenticated` | Optional: `{ "user_config": {...} }` | `201 Created` / `200 OK`<br>`PluginInstallationSerializer` | Installs plugin for current user with optional custom config. If already installed, ensures `is_enabled=True` and updates config. |
| `POST` | `/api/plugins/<identifier>/uninstall/` | `IsAuthenticated` | Optional: `{}` | `200 OK`<br>`{ "message": "...", "identifier": "...", "is_installed": false }` | Removes user plugin installation. Returns `400` if plugin was not installed. |
| `POST` | `/api/plugins/<identifier>/toggle/` | `IsAuthenticated` | Optional: `{ "is_enabled": bool, "user_config": {...} }` | `200 OK`<br>`PluginInstallationSerializer` | Toggles `is_enabled` status for user. If `is_enabled` is explicitly provided, sets it; otherwise flips boolean. |
| `GET` | `/api/plugins/topics/<topic_id>/` | `AllowAny` | None | `200 OK`<br>`[PluginTopicInstallationSerializer]` | Lists active topic plugin installations for given Topic. Returns `404` if topic does not exist. |
| `POST` | `/api/plugins/topics/<topic_id>/install/` | `IsAuthenticated`, `IsTopicAdminOrOwner` | Required: `{ "identifier": "quran", "topic_config": {...} }` | `201 Created` / `200 OK`<br>`PluginTopicInstallationSerializer` | Installs/enables plugin for the topic. Restricted to Topic Creator, Topic Admins, and Superusers. |
| `POST` | `/api/plugins/topics/<topic_id>/toggle/` | `IsAuthenticated`, `IsTopicAdminOrOwner` | Required: `{ "identifier": "quran" }`<br>Optional: `{ "is_enabled": bool, "topic_config": {...} }` | `200 OK`<br>`PluginTopicInstallationSerializer` | Toggles or updates plugin enablement on Topic. Restricted to Topic Creator/Admins. |
| `POST` | `/api/plugins/topics/<topic_id>/uninstall/` | `IsAuthenticated`, `IsTopicAdminOrOwner` | Required: `{ "identifier": "quran" }` | `200 OK`<br>`{ "message": "...", "identifier": "...", "is_installed": false }` | Uninstalls plugin from Topic. Restricted to Topic Creator/Admins. |
| `GET` | `/api/plugins/posts/<post_id>/references/` | `AllowAny` | None | `200 OK`<br>`[PostPluginReferenceSerializer]` | Retrieves all plugin references attached to a specific post. |
| `POST` | `/api/plugins/posts/<post_id>/references/` | `IsAuthenticated` | Required: `{ "plugin": "<uuid_or_identifier>", "resource_type": "ayah", "external_id": "1:1", "metadata": {...} }` | `201 Created`<br>`PostPluginReferenceSerializer` | Creates a decoupled content reference on a post. User must be post author, topic admin, or superuser. |

---

### 2.2 Permissions Blueprint (`backend/apps/plugin_system/permissions.py`)

```python
"""
Permissions for Tafakor Plugin System.
Validates topic ownership and administrative privileges for topic plugin installations.
"""
from rest_framework import permissions
from apps.notes.models import Topic


def is_topic_admin_or_owner(user, topic: Topic) -> bool:
    """
    Helper function checking if a user has administrative control over a topic.
    Returns True if:
    1. User is superuser.
    2. User is topic creator (created_by).
    3. User is listed in TopicAdmin for this topic.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if topic.created_by and topic.created_by == user:
        return True
    return topic.admins.filter(user=user).exists()


class IsTopicAdminOrOwner(permissions.BasePermission):
    """
    Permission class guarding Topic Plugin endpoints:
    - SAFE methods (GET, HEAD, OPTIONS) are allowed for all users.
    - Mutations (POST, PUT, PATCH, DELETE) require the user to be:
      1. Superuser, OR
      2. Topic Creator (`topic.created_by == request.user`), OR
      3. Topic Admin (`topic.admins.filter(user=request.user).exists()`).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Resolve Topic instance from various object types
        topic = None
        if isinstance(obj, Topic):
            topic = obj
        elif hasattr(obj, 'topic'):
            topic = obj.topic

        if not topic:
            return False

        return is_topic_admin_or_owner(request.user, topic)
```

---

### 2.3 Serializers Blueprint (`backend/apps/plugin_system/serializers.py`)

```python
"""
Serializers for Tafakor Plugin System.
Handles serialization and validation for Marketplace, User Installations,
Topic Installations, and Post Plugin References.
"""
import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, Post
from .models import Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference

User = get_user_model()


class PluginSerializer(serializers.ModelSerializer):
    """
    Marketplace listing serializer with dynamic user installation status.
    """
    is_installed = serializers.SerializerMethodField()
    is_enabled = serializers.SerializerMethodField()
    user_config = serializers.SerializerMethodField()

    class Meta:
        model = Plugin
        fields = [
            'id',
            'identifier',
            'name',
            'version',
            'description',
            'author',
            'icon',
            'manifest_version',
            'capabilities',
            'scopes',
            'is_active',
            'is_core',
            'is_installed',
            'is_enabled',
            'user_config',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def _get_user_installation(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        
        # Check pre-fetched mapping in context for O(1) bulk performance
        user_installations = self.context.get('user_installations')
        if user_installations is not None:
            return user_installations.get(obj.id) or user_installations.get(obj.identifier)
        
        return PluginInstallation.objects.filter(user=request.user, plugin=obj).first()

    def get_is_installed(self, obj) -> bool:
        installation = self._get_user_installation(obj)
        return installation is not None

    def get_is_enabled(self, obj) -> bool:
        installation = self._get_user_installation(obj)
        return installation.is_enabled if installation else False

    def get_user_config(self, obj) -> dict:
        installation = self._get_user_installation(obj)
        return installation.user_config if installation else {}


class PluginDetailSerializer(PluginSerializer):
    """
    Detailed serializer including full manifest settings schema and default configurations.
    """
    manifest = serializers.SerializerMethodField()

    class Meta(PluginSerializer.Meta):
        fields = PluginSerializer.Meta.fields + [
            'settings_schema',
            'default_config',
            'manifest',
        ]

    def get_manifest(self, obj) -> dict:
        return {
            'manifest_version': obj.manifest_version,
            'identifier': obj.identifier,
            'name': obj.name,
            'version': obj.version,
            'description': obj.description,
            'author': obj.author,
            'icon': obj.icon,
            'capabilities': obj.capabilities,
            'scopes': obj.scopes,
            'settings_schema': obj.settings_schema,
            'default_config': obj.default_config,
        }


class PluginInstallationSerializer(serializers.ModelSerializer):
    """
    Serializer for User-level plugin installations.
    """
    plugin_identifier = serializers.CharField(source='plugin.identifier', read_only=True)
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    plugin_icon = serializers.CharField(source='plugin.icon', read_only=True)
    plugin_version = serializers.CharField(source='plugin.version', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = PluginInstallation
        fields = [
            'id',
            'user',
            'user_phone',
            'plugin',
            'plugin_identifier',
            'plugin_name',
            'plugin_icon',
            'plugin_version',
            'is_enabled',
            'user_config',
            'installed_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_phone',
            'plugin',
            'plugin_identifier',
            'plugin_name',
            'plugin_icon',
            'plugin_version',
            'installed_at',
            'updated_at',
        ]


class PluginTopicInstallationSerializer(serializers.ModelSerializer):
    """
    Serializer for Topic-level plugin installations.
    """
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    plugin_identifier = serializers.CharField(source='plugin.identifier', read_only=True)
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    plugin_icon = serializers.CharField(source='plugin.icon', read_only=True)
    plugin_version = serializers.CharField(source='plugin.version', read_only=True)
    installed_by_phone = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PluginTopicInstallation
        fields = [
            'id',
            'topic',
            'topic_name',
            'plugin',
            'plugin_identifier',
            'plugin_name',
            'plugin_icon',
            'plugin_version',
            'installed_by',
            'installed_by_phone',
            'is_enabled',
            'topic_config',
            'installed_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'topic',
            'topic_name',
            'plugin',
            'plugin_identifier',
            'plugin_name',
            'plugin_icon',
            'plugin_version',
            'installed_by',
            'installed_by_phone',
            'installed_at',
            'updated_at',
        ]

    def get_installed_by_phone(self, obj):
        return obj.installed_by.phone if obj.installed_by else None


class PostPluginReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for Decoupled Content References (`PostPluginReference`).
    Permits posts to reference plugin resources (e.g. Ayah 1:1) without direct foreign keys.
    """
    plugin_identifier = serializers.CharField(source='plugin.identifier', read_only=True)
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)

    class Meta:
        model = PostPluginReference
        fields = [
            'id',
            'post',
            'plugin',
            'plugin_identifier',
            'plugin_name',
            'resource_type',
            'external_id',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'plugin_identifier', 'plugin_name']

    def validate(self, attrs):
        if not attrs.get('resource_type'):
            raise serializers.ValidationError({"resource_type": "Resource type cannot be empty."})
        if not attrs.get('external_id'):
            raise serializers.ValidationError({"external_id": "External ID cannot be empty."})
        return attrs


class PluginInstallRequestSerializer(serializers.Serializer):
    """Request payload for user plugin install."""
    user_config = serializers.DictField(required=False, default=dict)


class PluginToggleRequestSerializer(serializers.Serializer):
    """Request payload for user plugin toggle."""
    is_enabled = serializers.BooleanField(required=False, allow_null=True)
    user_config = serializers.DictField(required=False, allow_null=True)


class TopicPluginInstallRequestSerializer(serializers.Serializer):
    """Request payload for topic plugin install."""
    identifier = serializers.CharField(required=True, max_length=100)
    topic_config = serializers.DictField(required=False, default=dict)


class TopicPluginToggleRequestSerializer(serializers.Serializer):
    """Request payload for topic plugin toggle."""
    identifier = serializers.CharField(required=True, max_length=100)
    is_enabled = serializers.BooleanField(required=False, allow_null=True)
    topic_config = serializers.DictField(required=False, allow_null=True)


class TopicPluginUninstallRequestSerializer(serializers.Serializer):
    """Request payload for topic plugin uninstall."""
    identifier = serializers.CharField(required=True, max_length=100)
```

---

### 2.4 Views Blueprint (`backend/apps/plugin_system/views.py`)

```python
"""
API Views for Tafakor Plugin System.
Provides endpoints for Marketplace browsing, user plugin lifecycle,
topic plugin lifecycle, and post references.
"""
import logging
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from apps.notes.models import Topic, Post
from .models import Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference
from .serializers import (
    PluginSerializer,
    PluginDetailSerializer,
    PluginInstallationSerializer,
    PluginTopicInstallationSerializer,
    PostPluginReferenceSerializer,
    PluginInstallRequestSerializer,
    PluginToggleRequestSerializer,
    TopicPluginInstallRequestSerializer,
    TopicPluginToggleRequestSerializer,
    TopicPluginUninstallRequestSerializer,
)
from .permissions import IsTopicAdminOrOwner, is_topic_admin_or_owner

logger = logging.getLogger(__name__)


class PluginMarketplaceListView(APIView):
    """
    GET /api/plugins/
    Public Marketplace endpoint listing all active plugins.
    Annotates installation state for authenticated users.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = Plugin.objects.filter(is_active=True).order_by('name')

        # Optional filters
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(identifier__icontains=search) |
                Q(description__icontains=search)
            )

        capability = request.query_params.get('capability')
        if capability:
            queryset = queryset.filter(capabilities__contains=[capability])

        # Optimize user installations lookup
        user_installations = {}
        if request.user and request.user.is_authenticated:
            inst_qs = PluginInstallation.objects.filter(user=request.user)
            user_installations = {inst.plugin_id: inst for inst in inst_qs}

        serializer = PluginSerializer(
            queryset,
            many=True,
            context={'request': request, 'user_installations': user_installations}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class PluginDetailView(APIView):
    """
    GET /api/plugins/<identifier>/
    Public endpoint returning full plugin metadata, manifest, and settings schema.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, identifier):
        plugin = get_object_or_404(Plugin, identifier=identifier, is_active=True)
        serializer = PluginDetailSerializer(plugin, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PluginUserInstallView(APIView):
    """
    POST /api/plugins/<identifier>/install/
    Installs or re-enables a plugin for the requesting user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, identifier):
        plugin = get_object_or_404(Plugin, identifier=identifier, is_active=True)
        req_serializer = PluginInstallRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        user_config = req_serializer.validated_data.get('user_config', {})

        installation, created = PluginInstallation.objects.get_or_create(
            user=request.user,
            plugin=plugin,
            defaults={
                'is_enabled': True,
                'user_config': user_config or plugin.default_config
            }
        )

        if not created:
            installation.is_enabled = True
            if user_config:
                installation.user_config = user_config
            installation.save()

        # Trigger plugin lifecycle hook if registry loaded
        try:
            from .registry import plugin_registry
            plugin_cls = plugin_registry.get(identifier)
            if plugin_cls and hasattr(plugin_cls, 'on_install'):
                plugin_cls.on_install(user=request.user)
        except Exception as e:
            logger.warning(f"Plugin {identifier} on_install hook failed: {e}")

        serializer = PluginInstallationSerializer(installation)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class PluginUserUninstallView(APIView):
    """
    POST /api/plugins/<identifier>/uninstall/
    Uninstalls a plugin for the requesting user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, identifier):
        plugin = get_object_or_404(Plugin, identifier=identifier)
        installation = PluginInstallation.objects.filter(user=request.user, plugin=plugin).first()
        if not installation:
            return Response(
                {"error": "این پلاگین برای شما نصب نشده است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Trigger lifecycle hook
        try:
            from .registry import plugin_registry
            plugin_cls = plugin_registry.get(identifier)
            if plugin_cls and hasattr(plugin_cls, 'on_uninstall'):
                plugin_cls.on_uninstall(user=request.user)
        except Exception as e:
            logger.warning(f"Plugin {identifier} on_uninstall hook failed: {e}")

        installation.delete()
        return Response(
            {
                "message": f"پلاگین '{plugin.name}' با موفقیت حذف شد.",
                "identifier": identifier,
                "is_installed": False
            },
            status=status.HTTP_200_OK
        )


class PluginUserToggleView(APIView):
    """
    POST /api/plugins/<identifier>/toggle/
    Toggles `is_enabled` on a user plugin installation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, identifier):
        plugin = get_object_or_404(Plugin, identifier=identifier)
        installation = PluginInstallation.objects.filter(user=request.user, plugin=plugin).first()
        if not installation:
            return Response(
                {"error": "پلاگین برای این کاربر نصب نشده است. لطفاً ابتدا آن را نصب کنید."},
                status=status.HTTP_400_BAD_REQUEST
            )

        req_serializer = PluginToggleRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        explicit_enabled = req_serializer.validated_data.get('is_enabled')
        new_config = req_serializer.validated_data.get('user_config')

        if explicit_enabled is not None:
            installation.is_enabled = explicit_enabled
        else:
            installation.is_enabled = not installation.is_enabled

        if new_config is not None:
            installation.user_config = new_config

        installation.save()

        # Trigger lifecycle hooks
        try:
            from .registry import plugin_registry
            plugin_cls = plugin_registry.get(identifier)
            if plugin_cls:
                if installation.is_enabled and hasattr(plugin_cls, 'on_enable'):
                    plugin_cls.on_enable(user=request.user)
                elif not installation.is_enabled and hasattr(plugin_cls, 'on_disable'):
                    plugin_cls.on_disable(user=request.user)
        except Exception as e:
            logger.warning(f"Plugin {identifier} toggle hook failed: {e}")

        serializer = PluginInstallationSerializer(installation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TopicPluginListView(APIView):
    """
    GET /api/plugins/topics/<topic_id>/
    Lists active plugins installed on a specific topic.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id)
        installations = PluginTopicInstallation.objects.filter(
            topic=topic,
            plugin__is_active=True
        ).select_related('plugin', 'installed_by')

        serializer = PluginTopicInstallationSerializer(installations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TopicPluginInstallView(APIView):
    """
    POST /api/plugins/topics/<topic_id>/install/
    Installs/enables a plugin on a Topic.
    Restricted to Topic Owner, Topic Admins, and Superusers.
    """
    permission_classes = [permissions.IsAuthenticated, IsTopicAdminOrOwner]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id)
        self.check_object_permissions(request, topic)

        req_serializer = TopicPluginInstallRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        identifier = req_serializer.validated_data['identifier']
        topic_config = req_serializer.validated_data.get('topic_config', {})

        plugin = get_object_or_404(Plugin, identifier=identifier, is_active=True)

        installation, created = PluginTopicInstallation.objects.get_or_create(
            topic=topic,
            plugin=plugin,
            defaults={
                'is_enabled': True,
                'topic_config': topic_config or plugin.default_config,
                'installed_by': request.user
            }
        )

        if not created:
            installation.is_enabled = True
            if topic_config:
                installation.topic_config = topic_config
            installation.save()

        serializer = PluginTopicInstallationSerializer(installation)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class TopicPluginToggleView(APIView):
    """
    POST /api/plugins/topics/<topic_id>/toggle/
    Toggles or updates configuration of a plugin on a Topic.
    """
    permission_classes = [permissions.IsAuthenticated, IsTopicAdminOrOwner]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id)
        self.check_object_permissions(request, topic)

        req_serializer = TopicPluginToggleRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        identifier = req_serializer.validated_data['identifier']
        explicit_enabled = req_serializer.validated_data.get('is_enabled')
        topic_config = req_serializer.validated_data.get('topic_config')

        plugin = get_object_or_404(Plugin, identifier=identifier)
        installation = PluginTopicInstallation.objects.filter(topic=topic, plugin=plugin).first()
        if not installation:
            return Response(
                {"error": "این پلاگین روی این تاپیک نصب نشده است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if explicit_enabled is not None:
            installation.is_enabled = explicit_enabled
        else:
            installation.is_enabled = not installation.is_enabled

        if topic_config is not None:
            installation.topic_config = topic_config

        installation.save()
        serializer = PluginTopicInstallationSerializer(installation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TopicPluginUninstallView(APIView):
    """
    POST /api/plugins/topics/<topic_id>/uninstall/
    Uninstalls a plugin from a Topic.
    """
    permission_classes = [permissions.IsAuthenticated, IsTopicAdminOrOwner]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id)
        self.check_object_permissions(request, topic)

        req_serializer = TopicPluginUninstallRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        identifier = req_serializer.validated_data['identifier']

        plugin = get_object_or_404(Plugin, identifier=identifier)
        installation = PluginTopicInstallation.objects.filter(topic=topic, plugin=plugin).first()
        if not installation:
            return Response(
                {"error": "این پلاگین روی این تاپیک نصب نشده است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        installation.delete()
        return Response(
            {
                "message": f"پلاگین '{plugin.name}' با موفقیت از تاپیک حذف شد.",
                "identifier": identifier,
                "is_installed": False
            },
            status=status.HTTP_200_OK
        )


class PostPluginReferenceListCreateView(APIView):
    """
    GET /api/plugins/posts/<post_id>/references/ -> List references
    POST /api/plugins/posts/<post_id>/references/ -> Create reference
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        refs = PostPluginReference.objects.filter(post=post).select_related('plugin')
        serializer = PostPluginReferenceSerializer(refs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        # Check permissions: author, topic admin, or superuser
        is_author = (post.author == request.user)
        is_admin = is_topic_admin_or_owner(request.user, post.topic)
        if not (is_author or is_admin):
            raise PermissionDenied("شما اجازه ثبت ارجاع روی این پست را ندارید.")

        serializer = PostPluginReferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

---

### 2.5 URL Routing Blueprint (`backend/apps/plugin_system/urls.py`)

```python
"""
URL Routing for Tafakor Plugin System (`/api/plugins/`).
"""
from django.urls import path
from .views import (
    PluginMarketplaceListView,
    PluginDetailView,
    PluginUserInstallView,
    PluginUserUninstallView,
    PluginUserToggleView,
    TopicPluginListView,
    TopicPluginInstallView,
    TopicPluginToggleView,
    TopicPluginUninstallView,
    PostPluginReferenceListCreateView,
)

urlpatterns = [
    # Topic Plugin Management (Must precede <str:identifier> to prevent routing collisions)
    path('topics/<int:topic_id>/', TopicPluginListView.as_view(), name='topic-plugin-list'),
    path('topics/<int:topic_id>/install/', TopicPluginInstallView.as_view(), name='topic-plugin-install'),
    path('topics/<int:topic_id>/toggle/', TopicPluginToggleView.as_view(), name='topic-plugin-toggle'),
    path('topics/<int:topic_id>/uninstall/', TopicPluginUninstallView.as_view(), name='topic-plugin-uninstall'),

    # Post References
    path('posts/<int:post_id>/references/', PostPluginReferenceListCreateView.as_view(), name='post-plugin-reference-list-create'),

    # Marketplace & User Plugin Lifecycle
    path('', PluginMarketplaceListView.as_view(), name='plugin-marketplace-list'),
    path('<str:identifier>/', PluginDetailView.as_view(), name='plugin-detail'),
    path('<str:identifier>/install/', PluginUserInstallView.as_view(), name='plugin-user-install'),
    path('<str:identifier>/uninstall/', PluginUserUninstallView.as_view(), name='plugin-user-uninstall'),
    path('<str:identifier>/toggle/', PluginUserToggleView.as_view(), name='plugin-user-toggle'),
]
```

---

### 2.6 Root URL & Settings Integration

#### 1. Root URLConf Integration (`backend/note_platform/urls.py`)
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/notes/', include('apps.notes.urls')),
    path('api/bot/', include('apps.notes.bot_urls')),
    path('api/v1/donations/', include('apps.donations.urls')),
    path('api/donations/', include('apps.donations.urls')),
    path('api/plugins/', include('apps.plugin_system.urls')),  # Generic Plugin System Core
    
    # Media files serving
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
```

#### 2. Settings Integration (`backend/note_platform/settings.py`)
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
    'apps.plugin_system',  # Generic Plugin System Core
]

# ==============================================================================
# Tafakor Plugin System Configuration
# ==============================================================================
INSTALLED_TAFAKOR_PLUGINS = [
    # Empty by default in M1; M2 adds 'plugins.quran'
]

# Safely append dynamic plugin apps to Django INSTALLED_APPS
for _plugin_app in INSTALLED_TAFAKOR_PLUGINS:
    if _plugin_app not in INSTALLED_APPS:
        INSTALLED_APPS.append(_plugin_app)
```

---

## 3. Caveats & Edge Cases

1. **URL Route Precedence**:
   - `path('topics/<int:topic_id>/...', ...)` and `path('posts/<int:post_id>/...', ...)` MUST be defined before `path('<str:identifier>/', ...)` in `apps/plugin_system/urls.py` so that keywords `'topics'` or `'posts'` are not captured as a plugin identifier.
2. **Anonymous vs Authenticated Marketplace Annotations**:
   - `PluginSerializer` must safely inspect `request.user` without assuming the request is authenticated. When `request.user` is `AnonymousUser`, `is_installed=False`, `is_enabled=False`, and `user_config={}` are returned without throwing attribute or authentication errors.
3. **Bulk Performance Optimization**:
   - In `PluginMarketplaceListView`, user installations are queried once in a batch query (`PluginInstallation.objects.filter(user=request.user)`) and passed into the serializer context map `{plugin_id: installation}` to prevent N+1 query overhead.
4. **Topic Permissions Granularity**:
   - `IsTopicAdminOrOwner` handles three permission levels: superuser (bypasses check), creator (`topic.created_by == request.user`), and assigned admins (`topic.admins.filter(user=request.user).exists()`). Non-admin/non-owner authenticated users receive `403 Forbidden` on install/toggle/uninstall actions.
5. **Safe Plugin Toggle Flow**:
   - If a toggle request provides an explicit `is_enabled` boolean, it sets the value. If omitted, it flips the existing boolean state (`not installation.is_enabled`).
6. **Zero-Breaking-Change & Database Migration Independence**:
   - `PostPluginReference` stores `external_id` as a string (`CharField(max_length=255)`) and `metadata` as JSON. It does NOT create database foreign keys to plugin tables (`QuranAyah`, `QuranSurah`). If a plugin is uninstalled or deactivated, existing posts and references remain intact without schema integrity errors.

---

## 4. Conclusion

1. **Fully Decoupled Architecture**: All 9 REST API endpoints for marketplace listing, user lifecycle management, topic-level lifecycle management, and post content referencing have been designed with complete blueprints.
2. **Strict Non-Regression**: Integrating `apps.plugin_system` and `INSTALLED_TAFAKOR_PLUGINS` in `settings.py` and `note_platform/urls.py` introduces zero breaking changes to existing `notes`, `accounts`, `donations`, and `bot_runner` applications.
3. **Production-Ready Serializers & Permissions**: Serializers handle anonymous fallbacks, O(1) user installation lookups, and payload validation. Permissions cleanly mirror the existing `apps.notes` TopicAdmin model conventions.

---

## 5. Verification Method

To independently verify the REST API design, serializers, permissions, and settings integration:

### 5.1 Unit & API Test Scenarios (`backend/apps/plugin_system/tests/test_api.py`)
1. **Marketplace Listing**:
   - Send `GET /api/plugins/` as anonymous user: Verify status 200, response list has active plugins with `is_installed=False`, `is_enabled=False`.
   - Send `GET /api/plugins/` with user Token: Verify installed plugins reflect `is_installed=True` and correct `user_config`.
2. **User Plugin Lifecycle**:
   - Send `POST /api/plugins/quran/install/` with token: Verify status 201, `is_enabled=True`.
   - Send `POST /api/plugins/quran/toggle/` with token: Verify status 200, `is_enabled=False`.
   - Send `POST /api/plugins/quran/toggle/` with payload `{"is_enabled": true}`: Verify status 200, `is_enabled=True`.
   - Send `POST /api/plugins/quran/uninstall/` with token: Verify status 200, record removed from DB.
3. **Topic Plugin Lifecycle & Permissions**:
   - Create Topic with user A as owner. Appoint user B as TopicAdmin. User C is a regular member.
   - User A installs plugin on topic (`POST /api/plugins/topics/<id>/install/`): Verify status 201.
   - User B toggles plugin on topic (`POST /api/plugins/topics/<id>/toggle/`): Verify status 200.
   - User C attempts toggle: Verify status 403 Forbidden.
   - User C attempts uninstall: Verify status 403 Forbidden.
   - User A uninstalls plugin on topic: Verify status 200.
4. **Post Decoupled References**:
   - Create Post with `PostPluginReference` (`resource_type="ayah"`, `external_id="1:1"`).
   - Send `GET /api/plugins/posts/<post_id>/references/`: Verify status 200, returns list of references.

### 5.2 Isolation & Non-Regression Execution
```powershell
# Run backend test suite
pytest backend/apps/plugin_system/tests/ -v

# Run existing core test suites to confirm 0 regressions
pytest backend/apps/notes/tests.py backend/apps/accounts/tests.py backend/apps/donations/tests/ tests/integration/ -v
```
