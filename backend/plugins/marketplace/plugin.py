import json
from pathlib import Path
from typing import Dict, Any, Union
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.manifest import PluginManifest


class MarketplacePlugin(BasePlugin):
    """
    Official Tafakor Marketplace Plugin class.
    Discovered and loaded automatically by apps.plugin_system.registry.PluginRegistry.
    """

    def get_manifest(self) -> Union[PluginManifest, Dict[str, Any]]:
        manifest_path = Path(__file__).resolve().parent / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "manifest_version": 1,
            "identifier": "marketplace",
            "name": "Official Marketplace Plugin",
            "version": "1.0.0",
            "description": "Multi-vendor marketplace, book commerce, donation, escrow, and digital goods",
            "author": "Tafakor Core Team",
            "capabilities": ["composer_action", "mini_app", "topic_integration"],
            "scopes": ["read:content", "manage:topic"],
        }
