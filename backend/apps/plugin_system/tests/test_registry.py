"""
Unit tests for PluginRegistry singleton, autodiscovery, lifecycle hooks, and database synchronization.
"""
from django.test import TestCase, override_settings
from apps.plugin_system.registry import PluginRegistry, plugin_registry
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.models import Plugin
from apps.plugin_system.manifest import PluginManifest
from apps.plugin_system.exceptions import PluginRegistrationError
from django.contrib.auth import get_user_model
from apps.notes.models import Topic

User = get_user_model()


class MockSamplePlugin(BasePlugin):
    manifest = {
        "manifest_version": 1,
        "identifier": "sample-mock",
        "name": "پلاگین آزمایشی",
        "version": "1.0.0",
        "capabilities": ["composer_action", "mini_app"],
        "scopes": ["write:composer"],
        "settings_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer"}
            }
        },
        "default_config": {
            "limit": 10
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ready_called = False
        self.install_called = False
        self.uninstall_called = False
        self.enable_called = False
        self.disable_called = False

    def ready(self):
        self.ready_called = True

    def on_install(self, user=None, topic=None, config=None):
        self.install_called = True

    def on_uninstall(self, user=None, topic=None):
        self.uninstall_called = True

    def on_enable(self, user=None, topic=None):
        self.enable_called = True

    def on_disable(self, user=None, topic=None):
        self.disable_called = True


class PluginRegistryTestCase(TestCase):
    def setUp(self):
        self.registry = PluginRegistry()
        self.user = User.objects.create_user(phone="09124444444")
        self.topic = Topic.objects.create(name="تاپیک تستی", created_by=self.user)

    def test_registry_initialization_empty(self):
        """Registry initializes empty when no plugins are registered."""
        self.assertEqual(len(self.registry.all()), 0)
        self.assertIsNone(self.registry.get("non-existent"))
        self.assertFalse(self.registry.is_registered("non-existent"))

    def test_manual_plugin_registration(self):
        """Registering a BasePlugin instance stores it and makes it queryable."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)

        self.assertTrue(self.registry.is_registered("sample-mock"))
        self.assertEqual(self.registry.get("sample-mock"), plugin_instance)
        self.assertEqual(len(self.registry.all()), 1)
        self.assertTrue(plugin_instance.ready_called)
        self.assertEqual(plugin_instance.identifier, "sample-mock")
        self.assertEqual(plugin_instance.name, "پلاگین آزمایشی")
        self.assertEqual(plugin_instance.version, "1.0.0")

    def test_capability_filtering(self):
        """Verify get_plugins_with_capability retrieves matching plugins."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)

        matching = self.registry.get_plugins_with_capability("composer_action")
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].identifier, "sample-mock")

        empty_match = self.registry.get_plugins_with_capability("bot_action")
        self.assertEqual(len(empty_match), 0)

    def test_sync_with_database(self):
        """Registry sync_db() creates or updates records in the Plugin database table."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)
        self.registry.sync_db()

        db_plugin = Plugin.objects.get(identifier="sample-mock")
        self.assertEqual(db_plugin.name, "پلاگین آزمایشی")
        self.assertEqual(db_plugin.version, "1.0.0")
        self.assertTrue(db_plugin.is_active)
        self.assertEqual(db_plugin.default_config["limit"], 10)

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=[])
    def test_autodiscover_empty_setting(self):
        """Autodiscover with empty list completes without exceptions."""
        self.registry.autodiscover()
        self.assertEqual(len(self.registry.all()), 0)

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=["non.existent.module.path"])
    def test_autodiscover_handles_missing_module_gracefully(self):
        """Non-existent module in settings logs error and does not raise uncaught exception."""
        self.registry.autodiscover()
        self.assertEqual(len(self.registry.all()), 0)

    def test_lifecycle_hook_dispatch(self):
        """Lifecycle hooks on_install, on_uninstall, on_enable, on_disable are dispatched correctly."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)

        plugin_instance.on_install(user=self.user, config={"limit": 20})
        self.assertTrue(plugin_instance.install_called)

        plugin_instance.on_enable(user=self.user)
        self.assertTrue(plugin_instance.enable_called)

        plugin_instance.on_disable(user=self.user)
        self.assertTrue(plugin_instance.disable_called)

        plugin_instance.on_uninstall(user=self.user)
        self.assertTrue(plugin_instance.uninstall_called)

    def test_plugin_config_validation(self):
        """BasePlugin validate_config checks against manifest settings_schema."""
        plugin_instance = MockSamplePlugin()
        valid, err = plugin_instance.validate_config({"limit": 50})
        self.assertTrue(valid)
        self.assertIsNone(err)

        invalid, err = plugin_instance.validate_config({"limit": "not_an_int"})
        self.assertFalse(invalid)
        self.assertIsNotNone(err)

    def test_clear_registry(self):
        """Registry clear method purges in-memory plugin instances."""
        plugin_instance = MockSamplePlugin()
        self.registry.register(plugin_instance)
        self.assertEqual(len(self.registry.all()), 1)

        self.registry.clear()
        self.assertEqual(len(self.registry.all()), 0)
        self.assertFalse(self.registry.is_registered("sample-mock"))
