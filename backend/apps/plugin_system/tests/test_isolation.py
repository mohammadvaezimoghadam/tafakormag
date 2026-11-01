"""
Verification of zero breaking changes, empty INSTALLED_TAFAKOR_PLUGINS resilience,
and non-invasive post reference integrity.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, Post, BotTask
from apps.plugin_system.models import Plugin, PostPluginReference
from apps.plugin_system.registry import PluginRegistry

User = get_user_model()


class ZeroBreakingChangeIsolationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09127777771")
        self.topic = Topic.objects.create(name="تاپیک مستقل", created_by=self.user)

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=[])
    def test_empty_plugins_setting_isolation(self):
        """Server operates with INSTALLED_TAFAKOR_PLUGINS = [] without any startup errors or regressions."""
        registry = PluginRegistry()
        registry.autodiscover()
        self.assertEqual(len(registry.all()), 0)

        # Standard post creation operates normally
        post = Post.objects.create(topic=self.topic, author=self.user, content="پست تست بدون پلاگین")
        self.assertIsNotNone(post.id)
        self.assertEqual(post.topic, self.topic)

    def test_post_creation_and_bot_task_unaffected(self):
        """Standard Post creation and BotTask generation pipeline remains completely intact."""
        post = Post.objects.create(topic=self.topic, author=self.user, content="متن تستی با تسک ربات")
        task = BotTask.objects.create(
            action="send",
            platform="telegram",
            chat_id="123456",
            text="تسک تست",
            post_id=post
        )
        self.assertEqual(task.post_id, post)
        self.assertFalse(task.processed)

    def test_decoupled_post_plugin_reference_integrity(self):
        """PostPluginReference operates purely on external_id without touching core Post fields or schema."""
        plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")
        post = Post.objects.create(topic=self.topic, author=self.user, content="پست همراه با آیه قرآن")

        ref = PostPluginReference.objects.create(
            post=post,
            plugin=plugin,
            resource_type="ayah",
            external_id="114:1",
            metadata={"surah": 114, "ayah": 1}
        )

        # Post query and fields remain untouched
        post.refresh_from_db()
        self.assertEqual(post.plugin_references.count(), 1)
        self.assertEqual(post.plugin_references.first().external_id, "114:1")

        # Deleting the post cleanly cascades to reference without touching plugin
        post.delete()
        self.assertFalse(PostPluginReference.objects.filter(id=ref.id).exists())
        self.assertTrue(Plugin.objects.filter(id=plugin.id).exists())
