"""
Serializers for Tafakor Plugin System.
Handles serialization and validation for Marketplace, User Installations,
Topic Installations, and Post Plugin References.
"""
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
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
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
            'is_core': obj.is_core,
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


class PluginSummarySerializer(serializers.ModelSerializer):
    """Nested lightweight plugin representation."""
    class Meta:
        model = Plugin
        fields = ['id', 'identifier', 'name', 'icon', 'version', 'description']
        read_only_fields = fields


class PluginTopicInstallationSerializer(serializers.ModelSerializer):
    """
    Serializer for Topic-level plugin installations.
    """
    plugin = PluginSummarySerializer(read_only=True)
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
        extra_kwargs = {
            'post': {'required': False}
        }

    def to_internal_value(self, data):
        # Allow passing plugin by identifier string or UUID string or object
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        plugin_val = mutable_data.get('plugin')
        if isinstance(plugin_val, str):
            # Check if identifier instead of UUID
            plugin_obj = Plugin.objects.filter(identifier=plugin_val).first()
            if plugin_obj:
                mutable_data['plugin'] = str(plugin_obj.id)

        return super().to_internal_value(mutable_data)

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
