"""
Adversarial and Edge-Case Test Suite for Tafakor Plugin System REST APIs (/api/plugins/).
Stress tests authorization boundaries, edge cases, lifecycle operations,
malformed inputs, rapid state toggles, and data isolation.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.notes.models import Topic, TopicAdmin, Post
from apps.plugin_system.models import Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference

User = get_user_model()


class AdversarialMarketplaceAPITestCase(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(phone="09121111111")
        self.user_b = User.objects.create_user(phone="09122222222")

        self.active_plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن کریم",
            version="1.0.0",
            description="پلاگین رسمی قرآن کریم",
            capabilities=["composer_action", "mini_app"],
            scopes=["read:quran"],
            settings_schema={"type": "object", "properties": {"theme": {"type": "string"}}},
            default_config={"theme": "auto"},
            is_active=True,
            is_core=True
        )

        self.second_plugin = Plugin.objects.create(
            identifier="hadith",
            name="احادیث",
            version="0.9.0",
            description="پلاگین جامع احادیث",
            capabilities=["search_provider"],
            scopes=["read:content"],
            is_active=True,
            is_core=False
        )

        self.inactive_plugin = Plugin.objects.create(
            identifier="hidden-plugin",
            name="پلاگین مخفی غیرفعال",
            version="0.1.0",
            description="این نباید در مارکت‌پلیس یا دیتایل دیده شود",
            is_active=False
        )

    def test_marketplace_inactive_plugin_leakage(self):
        """Inactive plugins must NEVER be listed in marketplace."""
        res = self.client.get("/api/plugins/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [p["identifier"] for p in res.data]
        self.assertIn("quran", ids)
        self.assertIn("hadith", ids)
        self.assertNotIn("hidden-plugin", ids)

    def test_marketplace_search_edge_cases(self):
        """Search with special characters, unicode, SQL injection payloads, whitespace."""
        # 1. Unicode & Arabic/Persian
        res = self.client.get("/api/plugins/?search=قرآن")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["identifier"], "quran")

        # 2. SQL injection / regex special chars
        res_sql = self.client.get("/api/plugins/?search=' OR 1=1 --")
        self.assertEqual(res_sql.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_sql.data), 0)

        # 3. Special punctuation
        res_punct = self.client.get("/api/plugins/?search=~!@#$%^&*()_+")
        self.assertEqual(res_punct.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_punct.data), 0)

        # 4. Whitespace query
        res_space = self.client.get("/api/plugins/?search=   ")
        self.assertEqual(res_space.status_code, status.HTTP_200_OK)

    def test_marketplace_capability_filtering(self):
        """Capability filtering returns exact matches and handles non-existent caps."""
        res_match = self.client.get("/api/plugins/?capability=composer_action")
        self.assertEqual(res_match.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_match.data), 1)
        self.assertEqual(res_match.data[0]["identifier"], "quran")

        res_none = self.client.get("/api/plugins/?capability=non_existent_cap")
        self.assertEqual(res_none.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_none.data), 0)

    def test_user_installation_isolation_in_marketplace(self):
        """User A's installed plugins and config must not appear as installed for User B."""
        PluginInstallation.objects.create(
            user=self.user_a,
            plugin=self.active_plugin,
            is_enabled=True,
            user_config={"theme": "dark_gold"}
        )

        # User A view
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get("/api/plugins/")
        item_a = next(p for p in res_a.data if p["identifier"] == "quran")
        self.assertTrue(item_a["is_installed"])
        self.assertTrue(item_a["is_enabled"])
        self.assertEqual(item_a["user_config"], {"theme": "dark_gold"})

        # User B view
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get("/api/plugins/")
        item_b = next(p for p in res_b.data if p["identifier"] == "quran")
        self.assertFalse(item_b["is_installed"])
        self.assertFalse(item_b["is_enabled"])
        self.assertEqual(item_b["user_config"], {})

    def test_plugin_detail_inactive_returns_404(self):
        """Detail endpoint for an inactive plugin must return 404 Not Found."""
        res = self.client.get(f"/api/plugins/{self.inactive_plugin.identifier}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_plugin_detail_non_existent_returns_404(self):
        """Detail endpoint for a non-existent plugin identifier must return 404 Not Found."""
        res = self.client.get("/api/plugins/non-existent-plugin-123/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class AdversarialUserLifecycleAPITestCase(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(phone="09123333331")
        self.user_b = User.objects.create_user(phone="09123333332")

        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن",
            version="1.0.0",
            is_active=True,
            default_config={"reciter": "mishary", "font_size": 18}
        )

        self.inactive_plugin = Plugin.objects.create(
            identifier="inactive-test",
            name="غیرفعال",
            version="1.0.0",
            is_active=False
        )

    def test_install_unauthorized(self):
        """Unauthenticated user cannot install plugin (401)."""
        res = self.client.post(f"/api/plugins/{self.plugin.identifier}/install/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_install_inactive_plugin_returns_404(self):
        """Attempting to install an inactive plugin must return 404 Not Found."""
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(f"/api/plugins/{self.inactive_plugin.identifier}/install/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_install_non_existent_plugin_returns_404(self):
        """Attempting to install a non-existent plugin returns 404 Not Found."""
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post("/api/plugins/definitely-not-a-plugin/install/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_install_without_payload_uses_default_config(self):
        """Installing without specifying user_config defaults to plugin.default_config."""
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(f"/api/plugins/{self.plugin.identifier}/install/")
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        inst = PluginInstallation.objects.get(user=self.user_a, plugin=self.plugin)
        self.assertEqual(inst.user_config, {"reciter": "mishary", "font_size": 18})

    def test_uninstall_uninstalled_plugin_returns_400(self):
        """Uninstalling when not installed must return 400 Bad Request."""
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(f"/api/plugins/{self.plugin.identifier}/uninstall/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    def test_uninstall_cross_user_isolation(self):
        """User A cannot uninstall User B's installation."""
        PluginInstallation.objects.create(
            user=self.user_b,
            plugin=self.plugin,
            is_enabled=True
        )
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(f"/api/plugins/{self.plugin.identifier}/uninstall/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # User B's installation must still exist untouched
        self.assertTrue(PluginInstallation.objects.filter(user=self.user_b, plugin=self.plugin).exists())

    def test_toggle_uninstalled_plugin_returns_400(self):
        """Toggling a plugin not installed for this user returns 400 Bad Request."""
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(f"/api/plugins/{self.plugin.identifier}/toggle/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rapid_toggle_and_config_updates(self):
        """Perform rapid sequential toggles and config updates and verify consistency."""
        PluginInstallation.objects.create(
            user=self.user_a,
            plugin=self.plugin,
            is_enabled=True,
            user_config={"font_size": 14}
        )
        self.client.force_authenticate(user=self.user_a)
        url = f"/api/plugins/{self.plugin.identifier}/toggle/"

        # 1. Toggle to False
        res1 = self.client.post(url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertFalse(res1.data["is_enabled"])

        # 2. Toggle to True
        res2 = self.client.post(url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertTrue(res2.data["is_enabled"])

        # 3. Explicit toggle to False with config update
        res3 = self.client.post(url, {"is_enabled": False, "user_config": {"font_size": 22}}, format="json")
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertFalse(res3.data["is_enabled"])
        self.assertEqual(res3.data["user_config"], {"font_size": 22})

        # 4. Explicit toggle to True with another config update
        res4 = self.client.post(url, {"is_enabled": True, "user_config": {"font_size": 28}}, format="json")
        self.assertEqual(res4.status_code, status.HTTP_200_OK)
        self.assertTrue(res4.data["is_enabled"])
        self.assertEqual(res4.data["user_config"], {"font_size": 28})

        # Verify DB directly
        inst = PluginInstallation.objects.get(user=self.user_a, plugin=self.plugin)
        self.assertTrue(inst.is_enabled)
        self.assertEqual(inst.user_config, {"font_size": 28})


class AdversarialTopicPluginAPITestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(phone="09124444441")
        self.admin = User.objects.create_user(phone="09124444442")
        self.regular_member = User.objects.create_user(phone="09124444443")
        self.stranger = User.objects.create_user(phone="09124444444")
        self.superuser = User.objects.create_superuser(phone="09124444445", password="password123")

        self.topic = Topic.objects.create(name="تاپیک آزمایشی", created_by=self.owner)
        TopicAdmin.objects.create(topic=self.topic, user=self.admin)

        self.plugin = Plugin.objects.create(
            identifier="quran",
            name="قرآن",
            version="1.0.0",
            is_active=True,
            default_config={"show_arabic": True}
        )

        self.inactive_plugin = Plugin.objects.create(
            identifier="inactive-quran",
            name="غیرفعال",
            version="1.0.0",
            is_active=False
        )

    def test_topic_plugins_list_public(self):
        """GET /api/plugins/topics/<topic_id>/ is accessible to anonymous & returns active topic plugins."""
        PluginTopicInstallation.objects.create(
            topic=self.topic,
            plugin=self.plugin,
            installed_by=self.owner,
            is_enabled=True
        )
        res = self.client.get(f"/api/plugins/topics/{self.topic.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["plugin_identifier"], "quran")

    def test_topic_plugins_list_non_existent_topic(self):
        """GET /api/plugins/topics/<non_existent_id>/ returns 404 Not Found."""
        res = self.client.get("/api/plugins/topics/999999/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_topic_install_authorization_matrix(self):
        """
        Matrix of installation permissions on topic:
        - Anonymous: 401 Unauthorized
        - Stranger: 403 Forbidden
        - Regular member: 403 Forbidden
        - Topic Admin: 201 Created / 200 OK
        - Topic Owner: 201 Created / 200 OK
        - Superuser: 201 Created / 200 OK
        """
        url = f"/api/plugins/topics/{self.topic.id}/install/"
        payload = {"identifier": "quran", "topic_config": {"auto_verse": True}}

        # 1. Anonymous -> 401
        res_anon = self.client.post(url, payload, format="json")
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Stranger -> 403
        self.client.force_authenticate(user=self.stranger)
        res_stranger = self.client.post(url, payload, format="json")
        self.assertEqual(res_stranger.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Regular member -> 403
        self.client.force_authenticate(user=self.regular_member)
        res_member = self.client.post(url, payload, format="json")
        self.assertEqual(res_member.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Topic Admin -> 201/200
        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.post(url, payload, format="json")
        self.assertIn(res_admin.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        # 5. Topic Owner -> 200
        self.client.force_authenticate(user=self.owner)
        res_owner = self.client.post(url, payload, format="json")
        self.assertEqual(res_owner.status_code, status.HTTP_200_OK)

        # 6. Superuser -> 200
        self.client.force_authenticate(user=self.superuser)
        res_super = self.client.post(url, payload, format="json")
        self.assertEqual(res_super.status_code, status.HTTP_200_OK)

    def test_topic_install_inactive_plugin_returns_404(self):
        """Attempting to install an inactive plugin on a topic must return 404 Not Found."""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/plugins/topics/{self.topic.id}/install/"
        res = self.client.post(url, {"identifier": "inactive-quran"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_topic_install_missing_identifier_returns_400(self):
        """Installing without identifier in payload returns 400 Bad Request."""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/plugins/topics/{self.topic.id}/install/"
        res = self.client.post(url, {"topic_config": {}}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_topic_toggle_uninstalled_plugin_returns_400(self):
        """Toggling an uninstalled plugin on a topic returns 400 Bad Request."""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/plugins/topics/{self.topic.id}/toggle/"
        res = self.client.post(url, {"identifier": "quran"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_topic_toggle_permissions(self):
        """Only owner/admin/superuser can toggle topic plugins; others get 403."""
        PluginTopicInstallation.objects.create(
            topic=self.topic,
            plugin=self.plugin,
            installed_by=self.owner,
            is_enabled=True
        )
        url = f"/api/plugins/topics/{self.topic.id}/toggle/"
        payload = {"identifier": "quran"}

        # Regular user -> 403
        self.client.force_authenticate(user=self.regular_member)
        res_mem = self.client.post(url, payload, format="json")
        self.assertEqual(res_mem.status_code, status.HTTP_403_FORBIDDEN)

        # Admin -> 200
        self.client.force_authenticate(user=self.admin)
        res_adm = self.client.post(url, payload, format="json")
        self.assertEqual(res_adm.status_code, status.HTTP_200_OK)
        self.assertFalse(res_adm.data["is_enabled"])

    def test_topic_uninstall_uninstalled_plugin_returns_400(self):
        """Uninstalling a plugin not installed on topic returns 400 Bad Request."""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/plugins/topics/{self.topic.id}/uninstall/"
        res = self.client.post(url, {"identifier": "quran"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_topic_uninstall_permissions(self):
        """Only owner/admin/superuser can uninstall topic plugins; others get 403."""
        PluginTopicInstallation.objects.create(
            topic=self.topic,
            plugin=self.plugin,
            installed_by=self.owner,
            is_enabled=True
        )
        url = f"/api/plugins/topics/{self.topic.id}/uninstall/"
        payload = {"identifier": "quran"}

        # Regular member -> 403
        self.client.force_authenticate(user=self.regular_member)
        res_mem = self.client.post(url, payload, format="json")
        self.assertEqual(res_mem.status_code, status.HTTP_403_FORBIDDEN)

        # Superuser -> 200
        self.client.force_authenticate(user=self.superuser)
        res_super = self.client.post(url, payload, format="json")
        self.assertEqual(res_super.status_code, status.HTTP_200_OK)
        self.assertFalse(PluginTopicInstallation.objects.filter(topic=self.topic, plugin=self.plugin).exists())


class AdversarialPostPluginReferenceAPITestCase(APITestCase):
    def setUp(self):
        self.topic_owner = User.objects.create_user(phone="09127777771")
        self.topic_admin = User.objects.create_user(phone="09127777772")
        self.post_author = User.objects.create_user(phone="09127777773")
        self.other_user = User.objects.create_user(phone="09127777774")
        self.superuser = User.objects.create_superuser(phone="09127777775", password="password123")

        self.topic = Topic.objects.create(name="تاپیک ارجاعات", created_by=self.topic_owner)
        TopicAdmin.objects.create(topic=self.topic, user=self.topic_admin)

        self.post = Post.objects.create(topic=self.topic, author=self.post_author, content="پست حاوی آیه")
        self.plugin = Plugin.objects.create(identifier="quran", name="قرآن", version="1.0.0", is_active=True)

    def test_list_references_public_and_non_existent_post(self):
        """GET references on non-existent post returns 404; existing post returns 200 with list."""
        # Non-existent post
        res_404 = self.client.get("/api/plugins/posts/999999/references/")
        self.assertEqual(res_404.status_code, status.HTTP_404_NOT_FOUND)

        # Existing post
        PostPluginReference.objects.create(
            post=self.post,
            plugin=self.plugin,
            resource_type="ayah",
            external_id="1:1"
        )
        res_200 = self.client.get(f"/api/plugins/posts/{self.post.id}/references/")
        self.assertEqual(res_200.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_200.data), 1)
        self.assertEqual(res_200.data[0]["external_id"], "1:1")

    def test_create_reference_authorization_matrix(self):
        """
        Matrix of reference creation:
        - Anonymous: 401 Unauthorized
        - Other User (not author, not admin/owner): 403 Forbidden
        - Post Author: 201 Created
        - Topic Admin: 201 Created
        - Topic Owner: 201 Created
        - Superuser: 201 Created
        """
        url = f"/api/plugins/posts/{self.post.id}/references/"
        base_payload = {
            "plugin": "quran",
            "resource_type": "ayah",
            "external_id": "1:2"
        }

        # 1. Anonymous -> 401
        res_anon = self.client.post(url, base_payload, format="json")
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Other user -> 403
        self.client.force_authenticate(user=self.other_user)
        res_other = self.client.post(url, base_payload, format="json")
        self.assertEqual(res_other.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Post Author -> 201
        self.client.force_authenticate(user=self.post_author)
        res_author = self.client.post(url, {**base_payload, "external_id": "1:3"}, format="json")
        self.assertEqual(res_author.status_code, status.HTTP_201_CREATED)

        # 4. Topic Admin -> 201
        self.client.force_authenticate(user=self.topic_admin)
        res_admin = self.client.post(url, {**base_payload, "external_id": "1:4"}, format="json")
        self.assertEqual(res_admin.status_code, status.HTTP_201_CREATED)

        # 5. Topic Owner -> 201
        self.client.force_authenticate(user=self.topic_owner)
        res_owner = self.client.post(url, {**base_payload, "external_id": "1:5"}, format="json")
        self.assertEqual(res_owner.status_code, status.HTTP_201_CREATED)

        # 6. Superuser -> 201
        self.client.force_authenticate(user=self.superuser)
        res_super = self.client.post(url, {**base_payload, "external_id": "1:6"}, format="json")
        self.assertEqual(res_super.status_code, status.HTTP_201_CREATED)

    def test_create_reference_invalid_payloads(self):
        """Malformed payloads: missing plugin, invalid plugin identifier, empty resource_type, empty external_id."""
        self.client.force_authenticate(user=self.post_author)
        url = f"/api/plugins/posts/{self.post.id}/references/"

        # 1. Missing plugin
        res1 = self.client.post(url, {"resource_type": "ayah", "external_id": "2:1"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Non-existent plugin identifier
        res2 = self.client.post(url, {"plugin": "non_existent_plugin", "resource_type": "ayah", "external_id": "2:1"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Missing resource_type
        res3 = self.client.post(url, {"plugin": "quran", "external_id": "2:1"}, format="json")
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Empty external_id
        res4 = self.client.post(url, {"plugin": "quran", "resource_type": "ayah", "external_id": ""}, format="json")
        self.assertEqual(res4.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reference_with_uuid(self):
        """Pass plugin as UUID instead of identifier string."""
        self.client.force_authenticate(user=self.post_author)
        url = f"/api/plugins/posts/{self.post.id}/references/"
        payload = {
            "plugin": str(self.plugin.id),
            "resource_type": "surah",
            "external_id": "1",
            "metadata": {"name": "Al-Fatiha"}
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["plugin_identifier"], "quran")
        self.assertEqual(res.data["external_id"], "1")
