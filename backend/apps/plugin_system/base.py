from typing import Optional, Dict, Any, Tuple, Union
from .manifest import PluginManifest


class BasePlugin:
    """
    Base class that all Tafakor plugins must extend.
    """
    manifest: Optional[Union[PluginManifest, Dict[str, Any]]] = None

    def __init__(self, manifest: Optional[Union[PluginManifest, Dict[str, Any]]] = None):
        if manifest is not None:
            if isinstance(manifest, dict):
                self.manifest = PluginManifest.from_dict(manifest)
            else:
                self.manifest = manifest
        elif self.manifest is not None:
            if isinstance(self.manifest, dict):
                self.manifest = PluginManifest.from_dict(self.manifest)
        else:
            loaded_manifest = self.get_manifest()
            if isinstance(loaded_manifest, dict):
                self.manifest = PluginManifest.from_dict(loaded_manifest)
            else:
                self.manifest = loaded_manifest

    def get_manifest(self) -> Union[PluginManifest, Dict[str, Any]]:
        """Subclasses can override this to construct or load their manifest."""
        raise NotImplementedError("Plugin must define a manifest attribute or implement get_manifest().")

    @property
    def identifier(self) -> str:
        if self.manifest:
            return self.manifest.identifier
        return getattr(self, '_identifier', '')

    @property
    def name(self) -> str:
        if self.manifest:
            return self.manifest.name
        return ''

    @property
    def version(self) -> str:
        if self.manifest:
            return self.manifest.version
        return ''

    def ready(self) -> None:
        """Called upon registry initialization."""
        pass

    def on_install(self, user=None, topic=None, config: Optional[Dict[str, Any]] = None) -> None:
        """Hook called when installed by a user or on a topic."""
        pass

    def on_uninstall(self, user=None, topic=None) -> None:
        """Hook called when uninstalled."""
        pass

    def on_enable(self, user=None, topic=None) -> None:
        """Hook called when toggled on."""
        pass

    def on_disable(self, user=None, topic=None) -> None:
        """Hook called when toggled off."""
        pass

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates configuration against the plugin's settings_schema."""
        if not self.manifest or not self.manifest.settings_schema:
            return True, None
        try:
            import jsonschema
            jsonschema.validate(instance=config, schema=self.manifest.settings_schema)
            return True, None
        except Exception as e:
            return False, str(e)
