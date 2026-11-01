from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .validator import ManifestValidator


@dataclass
class PluginManifest:
    """
    Structured representation of a validated Tafakor Plugin Manifest.
    """
    manifest_version: int
    identifier: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    icon: str = "BookOpen"
    capabilities: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    settings_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    is_core: bool = False
    frontend: Dict[str, Any] = field(default_factory=dict)
    entry_point: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginManifest':
        validated = ManifestValidator.validate(data)
        return cls(
            manifest_version=validated['manifest_version'],
            identifier=validated['identifier'],
            name=validated['name'],
            version=validated['version'],
            description=validated.get('description', ''),
            author=validated.get('author', ''),
            icon=validated.get('icon', 'BookOpen'),
            capabilities=validated.get('capabilities', []),
            scopes=validated.get('scopes', []),
            settings_schema=validated.get('settings_schema', {}),
            default_config=validated.get('default_config', {}),
            is_core=validated.get('is_core', False),
            frontend=validated.get('frontend', {}),
            entry_point=validated.get('entry_point'),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'manifest_version': self.manifest_version,
            'identifier': self.identifier,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'icon': self.icon,
            'capabilities': self.capabilities,
            'scopes': self.scopes,
            'settings_schema': self.settings_schema,
            'default_config': self.default_config,
            'is_core': self.is_core,
            'frontend': self.frontend,
            'entry_point': self.entry_point,
        }
