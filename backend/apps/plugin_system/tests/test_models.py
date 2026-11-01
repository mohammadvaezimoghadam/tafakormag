"""
Unit tests for Plugin, PluginInstallation, PluginTopicInstallation, and PostPluginReference models.
"""
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, Post
from apps.plugin_system.models import (
    Plugin,
    PluginInstallation,
    PluginTopicInstallation,
    PostPluginReference,
)

User = get_user_model()


class PluginModelTestCase(TestCase):
    def setUp(self):
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن کریم",
            version="1.0.0",
            description="پلاگین رسمی قرآن کریم",
            author="Tafakor Team",
            icon="BookOpen",
            manifest_version=1,
            capabilities=["composer_action", "mini_app", "search_provider"],
            scopes=["read:quran", "write:composer"],
            settings_schema={"type": "object", "properties": {"default_edition": {"type": "string"}}},
            default_config={"default_edition": "quran-simple"},
            is_active=True,
            is_core=False
        )

    def test_plugin_creation_and_defaults(self):
        """Verify plugin UUID pk, string representation, and JSON defaults."""
        self.assertIsNotNone(self.plugin.id)
        self.assertEqual(str(self.plugin), "قرآن کریم (quran v1.0.0)")
        self.assertTrue(self.plugin.is_active)
        self.assertFalse(self.plugin.is_core)
        self.assertEqual(self.plugin.manifest_version, 1)

    def test_plugin_identifier_uniqueness(self):
        """Ensure duplicate identifier raises IntegrityError."""
        with self.assertRaises(IntegrityError):
            Plugin.objects.create(
                identifier="quran",
                name="قرآن تکراری",
                version="2.0.0"
            )

    def test_plugin_ordering(self):
        """Ensure plugins are ordered by name ascending."""
        Plugin.objects.create(identifier="analytics", name="آمار و تحلیل", version="1.0.0")
        plugins = list(Plugin.objects.all())
        self.assertEqual(plugins[0].identifier, "analytics")
        self.assertEqual(plugins[1].identifier, "quran")

    def test_plugin_json_fields_and_methods(self):
        """Verify nested JSON schema, list storage, and helper methods."""
        self.assertTrue(self.plugin.has_capability("composer_action"))
        self.assertFalse(self.plugin.has_capability("feed_card"))
        self.assertTrue(self.plugin.has_scope("read:quran"))
        self.assertFalse(self.plugin.has_scope("manage:topic"))
        self.assertEqual(self.plugin.default_config["default_edition"], "quran-simple")


class PluginInstallationModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09121111111")
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن",
            version="1.0.0",
            default_config={"edition": "simple", "font_size": 16}
        )
        self.installation = PluginInstallation.objects.create(
            user=self.user,
            plugin=self.plugin,
            is_enabled=True,
            user_config={"font_size": 18}
        )

    def test_installation_creation_and_defaults(self):
        """Verify user installation creation, UUID, and defaults."""
        self.assertIsNotNone(self.installation.id)
        self.assertTrue(self.installation.is_enabled)
        self.assertEqual(self.installation.user_config.get("font_size"), 18)
        self.assertIn("enabled", str(self.installation))

    def test_effective_config_merging(self):
        """Verify get_effective_config merges plugin defaults with user overrides."""
        effective = self.installation.get_effective_config()
        self.assertEqual(effective["edition"], "simple")
        self.assertEqual(effective["font_size"], 18)

    def test_user_plugin_unique_constraint(self):
        """Ensure same user cannot install the same plugin twice."""
        with self.assertRaises(IntegrityError):
            PluginInstallation.objects.create(
                user=self.user,
                plugin=self.plugin,
                is_enabled=False
            )

    def test_cascade_delete_user(self):
        """Deleting user deletes their plugin installations."""
        user_id = self.user.id
        self.user.delete()
        self.assertFalse(PluginInstallation.objects.filter(user_id=user_id).exists())

    def test_cascade_delete_plugin(self):
        """Deleting plugin cascades to all user installations."""
        plugin_id = self.plugin.id
        self.plugin.delete()
        self.assertFalse(PluginInstallation.objects.filter(plugin_id=plugin_id).exists())


class PluginTopicInstallationModelTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(phone="09122222222")
        self.topic = Topic.objects.create(name="تاپیک تدبر قرآن", created_by=self.owner)
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن",
            version="1.0.0",
            default_config={"badge": False, "mode": "reader"}
        )
        self.topic_install = PluginTopicInstallation.objects.create(
            topic=self.topic,
            plugin=self.plugin,
            installed_by=self.owner,
            is_enabled=True,
            topic_config={"badge": True}
        )

    def test_topic_installation_creation_and_config(self):
        """Verify topic plugin installation creation and config merging."""
        self.assertIsNotNone(self.topic_install.id)
        self.assertEqual(self.topic_install.topic, self.topic)
        self.assertEqual(self.topic_install.plugin, self.plugin)
        self.assertEqual(self.topic_install.installed_by, self.owner)
        self.assertTrue(self.topic_install.is_enabled)
        effective = self.topic_install.get_effective_config()
        self.assertEqual(effective["badge"], True)
        self.assertEqual(effective["mode"], "reader")

    def test_topic_plugin_unique_constraint(self):
        """Ensure duplicate (topic, plugin) pair raises IntegrityError."""
        with self.assertRaises(IntegrityError):
            PluginTopicInstallation.objects.create(
                topic=self.topic,
                plugin=self.plugin,
                is_enabled=False
            )

    def test_cascade_delete_topic(self):
        """Deleting topic cascades to all topic plugin installations."""
        topic_id = self.topic.id
        self.topic.delete()
        self.assertFalse(PluginTopicInstallation.objects.filter(topic_id=topic_id).exists())

    def test_set_null_installed_by_user(self):
        """Deleting installer user sets installed_by to NULL without deleting topic installation."""
        self.owner.delete()
        self.topic_install.refresh_from_db()
        self.assertIsNone(self.topic_install.installed_by)
        self.assertTrue(PluginTopicInstallation.objects.filter(id=self.topic_install.id).exists())


class PostPluginReferenceModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09123333333")
        self.topic = Topic.objects.create(name="تاپیک عمومی", created_by=self.user)
        self.post = Post.objects.create(topic=self.topic, author=self.user, content="متن تستی")
        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")
        self.ref = PostPluginReference.objects.create(
            post=self.post,
            plugin=self.plugin,
            resource_type="ayah",
            external_id="2:255",
            metadata={"surah": 2, "ayah": 255, "edition": "quran-simple"}
        )

    def test_post_reference_creation_and_attributes(self):
        """Verify PostPluginReference attributes, metadata, and decoupling."""
        self.assertIsNotNone(self.ref.id)
        self.assertEqual(self.ref.post, self.post)
        self.assertEqual(self.ref.plugin, self.plugin)
        self.assertEqual(self.ref.resource_type, "ayah")
        self.assertEqual(self.ref.external_id, "2:255")
        self.assertEqual(self.ref.metadata.get("surah"), 2)
        self.assertIn("2:255", str(self.ref))

    def test_cascade_delete_post(self):
        """Deleting Post cascades and removes PostPluginReference."""
        post_id = self.post.id
        self.post.delete()
        self.assertFalse(PostPluginReference.objects.filter(post_id=post_id).exists())

    def test_cascade_delete_plugin_keeps_post(self):
        """Deleting Plugin removes reference but preserves the original Post."""
        post_id = self.post.id
        self.plugin.delete()
        self.assertFalse(PostPluginReference.objects.filter(post_id=post_id).exists())
        self.assertTrue(Post.objects.filter(id=post_id).exists())
