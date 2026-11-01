"""
Unit tests for Quran Plugin Manifest and App Registration.
"""
import json
from pathlib import Path
from django.test import TestCase
from django.apps import apps
from apps.plugin_system.validator import ManifestValidator
from apps.plugin_system.manifest import PluginManifest
from plugins.quran.plugin import QuranPlugin


class QuranManifestTests(TestCase):
    def setUp(self):
        self.plugin_dir = Path(__file__).resolve().parent.parent
        self.manifest_path = self.plugin_dir / 'manifest.json'

    def test_manifest_file_exists_and_valid_json(self):
        self.assertTrue(self.manifest_path.exists())
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_manifest_schema_validation(self):
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        validated_dict = ManifestValidator.validate(data)
        manifest = PluginManifest.from_dict(validated_dict)
        self.assertEqual(manifest.manifest_version, 1)
        self.assertEqual(manifest.identifier, 'quran')
        self.assertEqual(manifest.name, 'Official Quran Plugin')
        self.assertEqual(manifest.version, '1.0.0')

        # Check capabilities
        self.assertIn('composer_action', manifest.capabilities)
        self.assertIn('mini_app', manifest.capabilities)
        self.assertIn('search_provider', manifest.capabilities)

        # Check scopes
        self.assertIn('read:content', manifest.scopes)
        self.assertIn('read:quran', manifest.scopes)

        # Check settings schema and default config
        self.assertIn('default_edition', manifest.default_config)
        self.assertIn('default_translation', manifest.default_config)
        self.assertEqual(manifest.default_config['default_edition'], 'quran-simple')
        self.assertEqual(manifest.default_config['default_translation'], 'fa.ansarian')

    def test_app_config_registered(self):
        app_config = apps.get_app_config('quran')
        self.assertEqual(app_config.name, 'plugins.quran')
        self.assertEqual(app_config.verbose_name, 'Official Quran Plugin')

    def test_plugin_class_manifest_loading(self):
        plugin = QuranPlugin()
        manifest_data = plugin.get_manifest()
        self.assertIsNotNone(manifest_data)
        validated = ManifestValidator.validate(manifest_data)
        self.assertEqual(validated['identifier'], 'quran')
