import uuid
from django.db import models
from django.conf import settings


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
