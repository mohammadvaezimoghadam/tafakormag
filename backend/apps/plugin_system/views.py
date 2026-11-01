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

        # Optional search filter
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(identifier__icontains=search) |
                Q(description__icontains=search)
            )

        # Optional capability filter
        capability = request.query_params.get('capability')
        if capability:
            all_plugins = list(queryset)
            matched_ids = [p.id for p in all_plugins if capability in (p.capabilities or [])]
            queryset = queryset.filter(id__in=matched_ids)

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
            plugin_instance = plugin_registry.get(identifier)
            if plugin_instance and hasattr(plugin_instance, 'on_install'):
                plugin_instance.on_install(user=request.user, config=installation.user_config)
        except Exception as e:
            logger.warning(f"Plugin {identifier} on_install hook error: {e}")

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
            plugin_instance = plugin_registry.get(identifier)
            if plugin_instance and hasattr(plugin_instance, 'on_uninstall'):
                plugin_instance.on_uninstall(user=request.user)
        except Exception as e:
            logger.warning(f"Plugin {identifier} on_uninstall hook error: {e}")

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
            plugin_instance = plugin_registry.get(identifier)
            if plugin_instance:
                if installation.is_enabled and hasattr(plugin_instance, 'on_enable'):
                    plugin_instance.on_enable(user=request.user)
                elif not installation.is_enabled and hasattr(plugin_instance, 'on_disable'):
                    plugin_instance.on_disable(user=request.user)
        except Exception as e:
            logger.warning(f"Plugin {identifier} toggle hook error: {e}")

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

        # Trigger lifecycle hook
        try:
            from .registry import plugin_registry
            plugin_instance = plugin_registry.get(identifier)
            if plugin_instance and hasattr(plugin_instance, 'on_install'):
                plugin_instance.on_install(topic=topic, config=installation.topic_config)
        except Exception as e:
            logger.warning(f"Plugin {identifier} topic on_install hook error: {e}")

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

        # Trigger lifecycle hooks
        try:
            from .registry import plugin_registry
            plugin_instance = plugin_registry.get(identifier)
            if plugin_instance:
                if installation.is_enabled and hasattr(plugin_instance, 'on_enable'):
                    plugin_instance.on_enable(topic=topic)
                elif not installation.is_enabled and hasattr(plugin_instance, 'on_disable'):
                    plugin_instance.on_disable(topic=topic)
        except Exception as e:
            logger.warning(f"Plugin {identifier} topic toggle hook error: {e}")

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

        # Trigger lifecycle hook
        try:
            from .registry import plugin_registry
            plugin_instance = plugin_registry.get(identifier)
            if plugin_instance and hasattr(plugin_instance, 'on_uninstall'):
                plugin_instance.on_uninstall(topic=topic)
        except Exception as e:
            logger.warning(f"Plugin {identifier} topic on_uninstall hook error: {e}")

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

        # Check permissions: author, topic admin/owner, or superuser
        is_author = (post.author_id == request.user.id)
        is_admin = is_topic_admin_or_owner(request.user, post.topic)
        if not (is_author or is_admin):
            raise PermissionDenied("شما اجازه ثبت ارجاع روی این پست را ندارید.")

        serializer = PostPluginReferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
