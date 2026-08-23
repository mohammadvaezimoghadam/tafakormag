"""
Comprehensive DRF API integration tests for /api/plugins/ marketplace, user, topic, and post reference endpoints.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, TopicAdmin, Post
from apps.plugin_system.models import Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference

User = get_user_model()


class PluginMarketplaceAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09125555551")
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن کریم",
            version="1.0.0",
            description="پلاگین قرآن",
            capabilities=["composer_action", "mini_app"],
            scopes=["read:quran"],
            is_active=True
        )
        self.inactive_plugin = Plugin.objects.create(
            identifier="disabled-plugin",
            name="غیرفعال",
            version="1.0.0",
            is_active=False
        )

    def test_list_plugins_anonymous(self):
        """GET /api/plugins/ returns 200 OK with active plugins and is_installed=False."""
        response = self.client.get("/api/plugins/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        identifiers = [item["identifier"] for item in response.data]
        self.assertIn("quran", identifiers)
        self.assertNotIn("disabled-plugin", identifiers)

        quran_item = next(item for item in response.data if item["identifier"] == "quran")
        self.assertFalse(quran_item.get("is_installed", False))
        self.assertFalse(quran_item.get("is_enabled", False))

    def test_list_plugins_search_filter(self):
        """Search query matches name, identifier, or description."""
        res_match = self.client.get("/api/plugins/?search=قرآن")
        self.assertEqual(len(res_match.data), 1)
        self.assertEqual(res_match.data[0]["identifier"], "quran")

        res_no_match = self.client.get("/api/plugins/?search=notfound123")
        self.assertEqual(len(res_no_match.data), 0)

    def test_list_plugins_capability_filter(self):
        """Filter plugins by capability keyword."""
        res = self.client.get("/api/plugins/?capability=composer_action")
        self.assertEqual(len(res.data), 1)

        res_empty = self.client.get("/api/plugins/?capability=feed_card")
        self.assertEqual(len(res_empty.data), 0)

    def test_list_plugins_authenticated_reflects_installation(self):
        """Authenticated user sees is_installed=True for their installed plugins."""
        PluginInstallation.objects.create(
            user=self.user,
            plugin=self.plugin,
            is_enabled=True,
            user_config={"theme": "dark"}
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/plugins/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        quran_item = next(item for item in response.data if item["identifier"] == "quran")
        self.assertTrue(quran_item["is_installed"])
        self.assertTrue(quran_item["is_enabled"])
        self.assertEqual(quran_item["user_config"].get("theme"), "dark")

    def test_plugin_detail_endpoint(self):
        """GET /api/plugins/<identifier>/ returns detailed manifest and settings schema."""
        response = self.client.get(f"/api/plugins/{self.plugin.identifier}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["identifier"], "quran")
        self.assertEqual(response.data["name"], "قرآن کریم")
        self.assertIn("manifest", response.data)

    def test_plugin_detail_not_found(self):
        """GET /api/plugins/non-existent/ returns 404 Not Found."""
        response = self.client.get("/api/plugins/non-existent/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserPluginLifecycleAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09125555552")
        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن کریم",
            version="1.0.0",
            settings_schema={"type": "object", "properties": {"theme": {"type": "string"}}},
            default_config={"theme": "light"}
        )

    def test_install_plugin_unauthenticated(self):
        """Unauthenticated install attempt returns 401 Unauthorized."""
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/install/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_install_plugin_success(self):
        """POST /api/plugins/<identifier>/install/ creates PluginInstallation with custom user_config."""
        self.client.force_authenticate(user=self.user)
        payload = {"user_config": {"theme": "dark"}}
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/install/", payload, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        install = PluginInstallation.objects.get(user=self.user, plugin=self.plugin)
        self.assertTrue(install.is_enabled)
        self.assertEqual(install.user_config.get("theme"), "dark")

    def test_reinstall_updates_config_and_reenables(self):
        """Re-installing updates user_config and sets is_enabled to True."""
        PluginInstallation.objects.create(
            user=self.user,
            plugin=self.plugin,
            is_enabled=False,
            user_config={"theme": "light"}
        )
        self.client.force_authenticate(user=self.user)
        payload = {"user_config": {"theme": "sepia"}}
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/install/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        install = PluginInstallation.objects.get(user=self.user, plugin=self.plugin)
        self.assertTrue(install.is_enabled)
        self.assertEqual(install.user_config.get("theme"), "sepia")

    def test_toggle_plugin_status(self):
        """POST /api/plugins/<identifier>/toggle/ flips is_enabled flag."""
        install = PluginInstallation.objects.create(user=self.user, plugin=self.plugin, is_enabled=True)
        self.client.force_authenticate(user=self.user)

        # Toggle to False
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/toggle/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        install.refresh_from_db()
        self.assertFalse(install.is_enabled)

        # Explicitly set to True
        response = self.client.post(
            f"/api/plugins/{self.plugin.identifier}/toggle/",
            {"is_enabled": True},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        install.refresh_from_db()
        self.assertTrue(install.is_enabled)

    def test_toggle_uninstalled_plugin_fails(self):
        """Toggling a plugin that is not installed returns 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/toggle/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_uninstall_plugin_success(self):
        """POST /api/plugins/<identifier>/uninstall/ deletes PluginInstallation."""
        PluginInstallation.objects.create(user=self.user, plugin=self.plugin)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/uninstall/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PluginInstallation.objects.filter(user=self.user, plugin=self.plugin).exists())

    def test_uninstall_uninstalled_plugin_fails(self):
        """Uninstalling a plugin that is not installed returns 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/plugins/{self.plugin.identifier}/uninstall/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TopicPluginLifecycleAPITestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(phone="09126666661")
        self.admin = User.objects.create_user(phone="09126666662")
        self.member = User.objects.create_user(phone="09126666663")

        self.topic = Topic.objects.create(name="تاپیک تخصصی", created_by=self.owner)
        TopicAdmin.objects.create(topic=self.topic, user=self.admin)

        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")

    def test_list_topic_plugins(self):
        """GET /api/plugins/topics/<topic_id>/ lists active plugins on topic."""
        PluginTopicInstallation.objects.create(topic=self.topic, plugin=self.plugin, is_enabled=True)
        response = self.client.get(f"/api/plugins/topics/{self.topic.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["plugin"]["identifier"], "quran")
        self.assertEqual(response.data[0]["plugin_identifier"], "quran")

    def test_list_topic_plugins_not_found(self):
        """Listing plugins for non-existent topic returns 404."""
        response = self.client.get("/api/plugins/topics/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_topic_install_permissions(self):
        """Non-admin member receives 403; Topic Owner and Topic Admin receive 201/200."""
        url = f"/api/plugins/topics/{self.topic.id}/install/"
        payload = {"identifier": "quran", "topic_config": {"auto_verse": True}}

        # 1. Member -> 403 Forbidden
        self.client.force_authenticate(user=self.member)
        res_member = self.client.post(url, payload, format="json")
        self.assertEqual(res_member.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Topic Admin -> 200/201 Created
        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.post(url, payload, format="json")
        self.assertIn(res_admin.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(PluginTopicInstallation.objects.filter(topic=self.topic, plugin=self.plugin).exists())

    def test_topic_toggle_and_uninstall_by_owner(self):
        """Topic owner can toggle and uninstall topic plugins."""
        install = PluginTopicInstallation.objects.create(
            topic=self.topic,
            plugin=self.plugin,
            is_enabled=True
        )
        self.client.force_authenticate(user=self.owner)

        # Toggle
        res_toggle = self.client.post(
            f"/api/plugins/topics/{self.topic.id}/toggle/",
            {"identifier": "quran"},
            format="json"
        )
        self.assertEqual(res_toggle.status_code, status.HTTP_200_OK)
        install.refresh_from_db()
        self.assertFalse(install.is_enabled)

        # Uninstall
        res_uninstall = self.client.post(
            f"/api/plugins/topics/{self.topic.id}/uninstall/",
            {"identifier": "quran"},
            format="json"
        )
        self.assertEqual(res_uninstall.status_code, status.HTTP_200_OK)
        self.assertFalse(PluginTopicInstallation.objects.filter(topic=self.topic, plugin=self.plugin).exists())


class PostPluginReferenceAPITestCase(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(phone="09128888881")
        self.admin = User.objects.create_user(phone="09128888882")
        self.other_user = User.objects.create_user(phone="09128888883")

        self.topic = Topic.objects.create(name="تاپیک پست‌ها", created_by=self.author)
        TopicAdmin.objects.create(topic=self.topic, user=self.admin)

        self.post = Post.objects.create(topic=self.topic, author=self.author, content="پست تستی")
        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0")

    def test_list_post_references(self):
        """GET /api/plugins/posts/<post_id>/references/ returns 200 OK and attached references."""
        PostPluginReference.objects.create(
            post=self.post,
            plugin=self.plugin,
            resource_type="ayah",
            external_id="1:1"
        )
        response = self.client.get(f"/api/plugins/posts/{self.post.id}/references/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["external_id"], "1:1")
        self.assertEqual(response.data[0]["plugin_identifier"], "quran")

    def test_create_post_reference_by_author(self):
        """Post author can attach a plugin reference to their post."""
        self.client.force_authenticate(user=self.author)
        payload = {
            "plugin": "quran",
            "resource_type": "ayah",
            "external_id": "2:255",
            "metadata": {"surah": 2, "ayah": 255}
        }
        response = self.client.post(
            f"/api/plugins/posts/{self.post.id}/references/",
            payload,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["external_id"], "2:255")
        self.assertTrue(PostPluginReference.objects.filter(post=self.post, external_id="2:255").exists())

    def test_create_post_reference_forbidden_for_other_users(self):
        """Non-author, non-admin user cannot attach reference to another user's post."""
        self.client.force_authenticate(user=self.other_user)
        payload = {
            "plugin": "quran",
            "resource_type": "ayah",
            "external_id": "2:255"
        }
        response = self.client.post(
            f"/api/plugins/posts/{self.post.id}/references/",
            payload,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
