import importlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from .base import BasePlugin
from .manifest import PluginManifest
from .exceptions import PluginRegistrationError

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Dynamic registry for Tafakor plugins. Autodiscovers plugins declared in
    settings.INSTALLED_TAFAKOR_PLUGINS and keeps DB records in sync safely.
    """

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._manifests: Dict[str, PluginManifest] = {}
        self._loaded: bool = False

    def autodiscover(self) -> None:
        """Discovers and registers all plugins from settings.INSTALLED_TAFAKOR_PLUGINS."""
        installed_plugin_apps = getattr(settings, 'INSTALLED_TAFAKOR_PLUGINS', [])
        for app_path in installed_plugin_apps:
            try:
                self.load_plugin(app_path)
            except Exception as e:
                logger.error(f"Failed to load Tafakor plugin '{app_path}': {e}", exc_info=True)

        self._loaded = True
        self.sync_to_db()

    def load_plugin(self, app_path: str) -> BasePlugin:
        """Loads, validates, and registers a single plugin package."""
        # 1. Try to load manifest.json in app directory if present
        manifest_data = None
        try:
            mod = importlib.import_module(app_path)
            if hasattr(mod, '__file__') and mod.__file__:
                manifest_file = Path(mod.__file__).parent / 'manifest.json'
                if manifest_file.exists():
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        manifest_data = json.load(f)
        except Exception as e:
            logger.debug(f"No manifest.json loaded from module path for {app_path}: {e}")

        # 2. Look for Plugin class in <app_path>.plugin or <app_path>
        plugin_cls: Optional[Type[BasePlugin]] = None
        for candidate_submod in ['.plugin', '']:
            try:
                submod = importlib.import_module(f"{app_path}{candidate_submod}")
                for attr_name in dir(submod):
                    attr = getattr(submod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                        plugin_cls = attr
                        break
                if plugin_cls:
                    break
            except ModuleNotFoundError:
                continue

        # 3. Instantiate plugin
        if plugin_cls:
            manifest_obj = PluginManifest.from_dict(manifest_data) if manifest_data else None
            plugin_instance = plugin_cls(manifest=manifest_obj)
        elif manifest_data:
            manifest_obj = PluginManifest.from_dict(manifest_data)
            plugin_instance = BasePlugin(manifest=manifest_obj)
        else:
            raise PluginRegistrationError(f"Cannot discover plugin entry point or manifest for '{app_path}'.")

        self.register(plugin_instance)
        return plugin_instance

    def register(self, plugin: BasePlugin) -> None:
        """Registers an instantiated BasePlugin in the memory registry."""
        if not plugin.manifest:
            try:
                manifest_loaded = plugin.get_manifest()
                if isinstance(manifest_loaded, dict):
                    plugin.manifest = PluginManifest.from_dict(manifest_loaded)
                else:
                    plugin.manifest = manifest_loaded
            except Exception as e:
                raise PluginRegistrationError(f"Plugin has no valid manifest: {e}")

        if isinstance(plugin.manifest, dict):
            plugin.manifest = PluginManifest.from_dict(plugin.manifest)

        identifier = plugin.identifier
        if not identifier:
            raise PluginRegistrationError("Plugin identifier cannot be empty.")

        self._plugins[identifier] = plugin
        self._manifests[identifier] = plugin.manifest
        plugin.ready()
        logger.info(f"Registered Tafakor plugin: {plugin.name} ({identifier})")

    def get(self, identifier: str) -> Optional[BasePlugin]:
        return self._plugins.get(identifier)

    def is_registered(self, identifier: str) -> bool:
        return identifier in self._plugins

    def get_all(self) -> List[BasePlugin]:
        return list(self._plugins.values())

    def all(self) -> List[BasePlugin]:
        """Alias for get_all."""
        return self.get_all()

    def get_manifests(self) -> List[PluginManifest]:
        return list(self._manifests.values())

    def get_plugins_with_capability(self, capability: str) -> List[BasePlugin]:
        return [
            p for p in self._plugins.values()
            if p.manifest and capability in p.manifest.capabilities
        ]

    def sync_to_db(self) -> None:
        """
        Synchronizes registered plugins to the database Plugin table.
        Gracefully handles early migration phases where DB tables do not exist yet.
        """
        try:
            from .models import Plugin
            for identifier, manifest in self._manifests.items():
                Plugin.objects.update_or_create(
                    identifier=identifier,
                    defaults={
                        'name': manifest.name,
                        'version': manifest.version,
                        'description': manifest.description,
                        'author': manifest.author,
                        'icon': manifest.icon,
                        'manifest_version': manifest.manifest_version,
                        'capabilities': manifest.capabilities,
                        'scopes': manifest.scopes,
                        'settings_schema': manifest.settings_schema,
                        'default_config': manifest.default_config,
                        'is_core': manifest.is_core,
                        'is_active': True,
                    }
                )
        except (OperationalError, ProgrammingError) as db_err:
            logger.info(f"Skipping plugin DB sync during migration phase: {db_err}")
        except Exception as e:
            logger.warning(f"Plugin DB sync encountered non-fatal error: {e}")

    def sync_db(self) -> None:
        """Alias for sync_to_db."""
        self.sync_to_db()

    def clear(self) -> None:
        """For testing purposes: resets in-memory registry."""
        self._plugins.clear()
        self._manifests.clear()
        self._loaded = False


plugin_registry = PluginRegistry()
