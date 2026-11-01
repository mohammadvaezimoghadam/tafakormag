from django.apps import AppConfig


class PluginSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.plugin_system'
    verbose_name = 'Tafakor Plugin System'

    def ready(self):
        # Trigger autodiscovery when Django finishes initializing apps
        try:
            from .registry import plugin_registry
            plugin_registry.autodiscover()
        except Exception:
            pass
