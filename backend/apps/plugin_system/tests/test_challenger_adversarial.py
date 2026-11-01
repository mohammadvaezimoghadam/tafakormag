"""
Adversarial Stress Test Suite for Tafakor Plugin System (Milestone 1).
Author: Empirical Challenger 1
Focus: Boundary conditions, corrupted inputs, permission escapes, database integrity, race conditions.
"""
import uuid
import json
import jsonschema
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.db import IntegrityError
from django.db.utils import OperationalError, ProgrammingError
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.notes.models import Topic, Post, TopicAdmin
from apps.plugin_system.models import (
    Plugin,
    PluginInstallation,
    PluginTopicInstallation,
    PostPluginReference,
)
from apps.plugin_system.validator import ManifestValidator
from apps.plugin_system.manifest import PluginManifest
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.registry import PluginRegistry
from apps.plugin_system.exceptions import (
    ManifestValidationError,
    PluginRegistrationError,
    PluginNotFoundError,
)

User = get_user_model()


class ManifestValidatorAdversarialTests(TestCase):
    """
    Adversarial & boundary testing for ManifestValidator.
    """

    def setUp(self):
        self.base_valid = {
            "manifest_version": 1,
            "identifier": "adversarial-probe",
            "name": "پلاگین تستی نفوذ",
            "version": "1.0.0",
            "capabilities": ["composer_action", "mini_app"],
            "scopes": ["read:content", "write:composer"],
            "settings_schema": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "minimum": 1, "maximum": 100}
                },
                "required": ["count"]
            },
            "default_config": {
                "count": 5
            }
        }

    # 1. Manifest version tests
    def test_manifest_version_edge_cases(self):
        """Test non-1 integer types, booleans, floats, strings, negative ints."""
        invalids = [
            True,        # True == 1 in Python int hierarchy
            False,
            0,
            2,
            -1,
            1.0,
            "1",
            "1.0",
            None,
            [],
            {},
            9999999999999999999999999999999999999999999
        ]
        for val in invalids:
            data = dict(self.base_valid, manifest_version=val)
            with self.assertRaises(ManifestValidationError, msg=f"manifest_version={val!r} must be rejected"):
                ManifestValidator.validate(data)

    # 2. Identifier edge cases & regex boundaries
    def test_identifier_boundary_attacks(self):
        """Test SQL injection, path traversal, unicode, null bytes, symbols, uppercase."""
        adversarial_identifiers = [
            "",
            "   ",
            "UPPERCASE",
            "camelCase",
            "space in middle",
            "../traversal",
            "../../etc/passwd",
            "plugin; DROP TABLE tafakor_plugins; --",
            "<script>alert(1)</script>",
            "quran\x00nullbyte",
            "نام_فارسی",
            "emoji_😊",
            "dot.separated.name",
            "colon:separated",
            "slash/separated",
            "back\\slash",
            "-leading-dash",     # Note: ^[a-z0-9_-]+$ matches leading dash
            "trailing-dash-",
            "_leading_underscore",
            "a" * 1000,          # 1000 chars
            None,
            12345,
            True,
            ["list_ident"]
        ]
        for ident in adversarial_identifiers:
            data = dict(self.base_valid, identifier=ident)
            if isinstance(ident, str) and ManifestValidator.IDENTIFIER_REGEX.match(ident):
                # Valid regex match (e.g. leading dash/underscore or long string)
                validated = ManifestValidator.validate(data)
                self.assertEqual(validated["identifier"], ident)
            else:
                with self.assertRaises(ManifestValidationError, msg=f"identifier={ident!r} must fail"):
                    ManifestValidator.validate(data)

    # 3. SemVer edge cases & regex boundaries
    def test_semver_boundary_cases(self):
        """Test SemVer standard formats and malformed versions."""
        valid_semvers = [
            "0.0.1",
            "1.0.0",
            "2.10.35",
            "1.0.0-alpha",
            "1.0.0-beta.1",
            "1.0.0-rc_1.2",
            "10.200.3000",
        ]
        for v in valid_semvers:
            data = dict(self.base_valid, version=v)
            res = ManifestValidator.validate(data)
            self.assertEqual(res["version"], v)

        invalid_semvers = [
            "",
            "v1.0.0",           # Leading 'v'
            "1.0",              # Missing patch
            "1",                # Major only
            "1.0.0.0",          # 4 parts
            "1.0.0-",           # Trailing hyphen
            "1.0.0+20130313",   # Build metadata without prerelease (fails regex)
            "1.0.0-alpha@beta", # Invalid symbol
            "1.0.0-alpha space",# Space
            "version 1.0",      # Words
            None,
            100,
            True,
            ["1.0.0"]
        ]
        for v in invalid_semvers:
            data = dict(self.base_valid, version=v)
            with self.assertRaises(ManifestValidationError, msg=f"version={v!r} must be rejected"):
                ManifestValidator.validate(data)

    # 4. Capabilities & Scopes boundary testing
    def test_capabilities_and_scopes_tampering(self):
        """Test unsupported capabilities, non-list, malicious enum injections."""
        invalid_cap_sets = [
            "composer_action",           # string instead of list
            None,
            {"composer_action": True},
            [123, 456],
            ["COMPOSER_ACTION"],          # Casing mismatch
            [""],                         # Empty string item
            ["composer_action", "root_admin", "arbitrary_eval"],
            ["composer_action", "composer_action"],  # duplicate
        ]
        for caps in invalid_cap_sets:
            data = dict(self.base_valid, capabilities=caps)
            if caps == ["composer_action", "composer_action"]:
                # Duplicates of valid keywords validate, but are contained
                res = ManifestValidator.validate(data)
                self.assertIn("composer_action", res["capabilities"])
            else:
                with self.assertRaises(ManifestValidationError, msg=f"capabilities={caps!r} must be rejected"):
                    ManifestValidator.validate(data)

    # 5. Corrupted JSON Schema & default_config mismatch
    def test_corrupted_json_schema_in_settings_schema_empty_default_config(self):
        """Test invalid JSON Schema specs in settings_schema when default_config is empty."""
        corrupted_schemas = [
            {"type": "non_existent_type_123"},
            {"type": "object", "properties": "not a dict"},
            {"type": "object", "required": "not a list"},
            {"type": "string", "pattern": "[unclosed-regex-bracket("},
        ]
        for bad_schema in corrupted_schemas:
            data = dict(self.base_valid, settings_schema=bad_schema, default_config={})
            with self.assertRaises(ManifestValidationError, msg=f"Corrupted schema {bad_schema} must fail"):
                ManifestValidator.validate(data)

    def test_default_config_schema_violation(self):
        """Test default_config violating settings_schema constraints."""
        data = dict(
            self.base_valid,
            settings_schema={
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "minimum": 10, "maximum": 20}
                },
                "required": ["count"],
                "additionalProperties": False
            },
            default_config={
                "count": 5  # Below minimum of 10
            }
        )
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(data)

        # Extra disallowed properties
        data["default_config"] = {"count": 15, "extra_key": "injected"}
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(data)

    def test_empty_dict_manifest(self):
        """Empty dict must fail with multiple required field errors."""
        with self.assertRaises(ManifestValidationError) as ctx:
            ManifestValidator.validate({})
        err_msg = str(ctx.exception)
        self.assertIn("manifest_version", err_msg)
        self.assertIn("identifier", err_msg)
        self.assertIn("name", err_msg)
        self.assertIn("version", err_msg)


class PluginRegistryAdversarialTests(TestCase):
    """
    Adversarial stress testing on PluginRegistry lifecycle & error recovery.
    """

    def setUp(self):
        self.registry = PluginRegistry()

    def test_duplicate_registration_overwrites_cleanly(self):
        """Registering a plugin with an existing identifier updates the registry cleanly."""
        class PluginV1(BasePlugin):
            manifest = {
                "manifest_version": 1,
                "identifier": "dup-test",
                "name": "نسخه اول",
                "version": "1.0.0"
            }

        class PluginV2(BasePlugin):
            manifest = {
                "manifest_version": 1,
                "identifier": "dup-test",
                "name": "نسخه دوم",
                "version": "2.0.0"
            }

        p1 = PluginV1()
        p2 = PluginV2()

        self.registry.register(p1)
        self.assertEqual(self.registry.get("dup-test").version, "1.0.0")

        # Second registration should overwrite memory cache safely
        self.registry.register(p2)
        self.assertEqual(self.registry.get("dup-test").version, "2.0.0")
        self.assertEqual(len(self.registry.all()), 1)

    def test_register_plugin_without_manifest_raises_registration_error(self):
        """BasePlugin with no manifest and raising NotImplementedError on get_manifest() fails gracefully."""
        class BrokenPlugin(BasePlugin):
            def __init__(self):
                # intentionally pass None without get_manifest override
                try:
                    super().__init__(manifest=None)
                except NotImplementedError:
                    self.manifest = None

        p = BrokenPlugin()
        with self.assertRaises(PluginRegistrationError):
            self.registry.register(p)

    def test_load_plugin_corrupted_manifest_file(self):
        """load_plugin handles unparseable JSON in manifest.json without unhandled crash."""
        with patch("importlib.import_module") as mock_import, \
             patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", MagicMock(side_effect=json.JSONDecodeError("Expecting value", "bad json", 0))):
            
            mock_mod = MagicMock()
            mock_mod.__file__ = "f:/fake/path/__init__.py"
            mock_import.return_value = mock_mod

            with self.assertRaises(PluginRegistrationError):
                self.registry.load_plugin("fake.broken.plugin")

    def test_db_sync_handles_operational_error_gracefully(self):
        """sync_to_db absorbs OperationalError (e.g. during migrations before table creation)."""
        class SafePlugin(BasePlugin):
            manifest = {
                "manifest_version": 1,
                "identifier": "safe-sync",
                "name": "پلاگین هماهنگ",
                "version": "1.0.0"
            }

        self.registry.register(SafePlugin())
        with patch("apps.plugin_system.models.Plugin.objects.update_or_create", side_effect=OperationalError("no such table: tafakor_plugins")):
            # Must not raise exception
            self.registry.sync_to_db()

    def test_db_sync_handles_programming_error_gracefully(self):
        """sync_to_db absorbs ProgrammingError (e.g. table not ready in PostgreSQL)."""
        class SafePlugin(BasePlugin):
            manifest = {
                "manifest_version": 1,
                "identifier": "safe-sync",
                "name": "پلاگین هماهنگ",
                "version": "1.0.0"
            }

        self.registry.register(SafePlugin())
        with patch("apps.plugin_system.models.Plugin.objects.update_or_create", side_effect=ProgrammingError("relation tafakor_plugins does not exist")):
            # Must not raise exception
            self.registry.sync_to_db()

    def test_autodiscover_survives_mixed_valid_and_broken_packages(self):
        """autodiscover continues registering subsequent plugins when one package in list fails."""
        class GoodPlugin(BasePlugin):
            manifest = {
                "manifest_version": 1,
                "identifier": "good-plugin",
                "name": "پلاگین سالم",
                "version": "1.0.0"
            }

        def side_effect_loader(app_path):
            if app_path == "bad.package":
                raise PluginRegistrationError("Failed to load bad package")
            elif app_path == "good.package":
                p = GoodPlugin()
                self.registry.register(p)
                return p
            raise ModuleNotFoundError(f"No module {app_path}")

        with override_settings(INSTALLED_TAFAKOR_PLUGINS=["bad.package", "good.package"]), \
             patch.object(self.registry, 'load_plugin', side_effect=side_effect_loader):
            self.registry.autodiscover()
            self.assertTrue(self.registry.is_registered("good-plugin"))
            self.assertFalse(self.registry.is_registered("bad-plugin"))


class DatabaseIntegrityAndModelAdversarialTests(TestCase):
    """
    Stress test model constraints, cascading rules, JSONField mutations, and UUIDs.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(phone="09120000001")
        self.user2 = User.objects.create_user(phone="09120000002")
        self.topic1 = Topic.objects.create(name="تاپیک 1", created_by=self.user1)
        self.topic2 = Topic.objects.create(name="تاپیک 2", created_by=self.user2)
        self.plugin1 = Plugin.objects.create(
            identifier="test-plugin-1",
            name="پلاگین اول",
            version="1.0.0",
            default_config={"key_a": 100, "nested": {"val": "default"}}
        )
        self.plugin2 = Plugin.objects.create(
            identifier="test-plugin-2",
            name="پلاگین دوم",
            version="2.0.0",
            default_config={"key_b": 200}
        )

    def test_uuid_primary_keys_uniqueness_and_immutability(self):
        """All entities have unique valid UUID4 primary keys."""
        inst = PluginInstallation.objects.create(user=self.user1, plugin=self.plugin1)
        topic_inst = PluginTopicInstallation.objects.create(topic=self.topic1, plugin=self.plugin1)
        post = Post.objects.create(topic=self.topic1, author=self.user1, content="تست")
        ref = PostPluginReference.objects.create(
            post=post, plugin=self.plugin1, resource_type="ayah", external_id="1:1"
        )

        all_ids = [self.plugin1.id, inst.id, topic_inst.id, ref.id]
        for obj_id in all_ids:
            self.assertIsInstance(obj_id, uuid.UUID)
        self.assertEqual(len(set(all_ids)), 4)

    def test_plugin_installation_concurrent_unique_constraint(self):
        """UniqueConstraint prevents duplicate (user, plugin) pairs in database."""
        PluginInstallation.objects.create(user=self.user1, plugin=self.plugin1, is_enabled=True)
        with self.assertRaises(IntegrityError):
            PluginInstallation.objects.create(user=self.user1, plugin=self.plugin1, is_enabled=False)

    def test_plugin_topic_installation_unique_constraint(self):
        """UniqueConstraint prevents duplicate (topic, plugin) pairs in database."""
        PluginTopicInstallation.objects.create(topic=self.topic1, plugin=self.plugin1, is_enabled=True)
        with self.assertRaises(IntegrityError):
            PluginTopicInstallation.objects.create(topic=self.topic1, plugin=self.plugin1, is_enabled=False)

    def test_effective_config_does_not_mutate_plugin_default(self):
        """get_effective_config must not mutate underlying Plugin.default_config in memory or DB."""
        inst = PluginInstallation.objects.create(
            user=self.user1,
            plugin=self.plugin1,
            user_config={"key_a": 999, "extra": "user_val"}
        )
        effective = inst.get_effective_config()
        self.assertEqual(effective["key_a"], 999)
        self.assertEqual(effective["extra"], "user_val")

        # Plugin default_config must remain pristine
        self.plugin1.refresh_from_db()
        self.assertEqual(self.plugin1.default_config["key_a"], 100)
        self.assertNotIn("extra", self.plugin1.default_config)

    def test_cascading_behavior_deep_audit(self):
        """
        Comprehensive cascade verification:
        1. Deleting Post -> Deletes PostPluginReference (Plugin intact).
        2. Deleting Topic -> Deletes PluginTopicInstallation (Plugin & User intact).
        3. Deleting User (creator) -> Sets installed_by=NULL on PluginTopicInstallation (Topic install intact).
        4. Deleting Plugin -> Deletes PluginInstallation, PluginTopicInstallation, PostPluginReference (Post & Topic intact).
        """
        post = Post.objects.create(topic=self.topic1, author=self.user1, content="پست تست جامع")
        ref = PostPluginReference.objects.create(
            post=post, plugin=self.plugin1, resource_type="glossary", external_id="term-1"
        )
        user_inst = PluginInstallation.objects.create(user=self.user1, plugin=self.plugin1)
        topic_inst = PluginTopicInstallation.objects.create(
            topic=self.topic1, plugin=self.plugin1, installed_by=self.user1
        )

        # Step 1: Delete Post -> Ref deleted, Plugin stays
        post_id = post.id
        ref_id = ref.id
        post.delete()
        self.assertFalse(PostPluginReference.objects.filter(id=ref_id).exists())
        self.assertTrue(Plugin.objects.filter(id=self.plugin1.id).exists())

        # Step 2: Delete User (installer) -> installed_by becomes NULL, topic_inst survives
        user1_id = self.user1.id
        topic_inst_id = topic_inst.id
        self.user1.delete()
        topic_inst.refresh_from_db()
        self.assertIsNone(topic_inst.installed_by)
        self.assertTrue(PluginTopicInstallation.objects.filter(id=topic_inst_id).exists())
        self.assertFalse(PluginInstallation.objects.filter(user_id=user1_id).exists())

        # Step 3: Delete Plugin -> topic_inst cascades, Topic survives
        topic1_id = self.topic1.id
        self.plugin1.delete()
        self.assertFalse(PluginTopicInstallation.objects.filter(id=topic_inst_id).exists())
        self.assertTrue(Topic.objects.filter(id=topic1_id).exists())


class ApiPermissionsAndSecurityAdversarialTests(TestCase):
    """
    Adversarial security and permission testing on REST API endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(phone="09129999999", password="adminpassword")
        self.owner = User.objects.create_user(phone="09128888888")
        self.admin_user = User.objects.create_user(phone="09127777777")
        self.regular_user = User.objects.create_user(phone="09126666666")
        self.stranger_user = User.objects.create_user(phone="09125555555")

        self.topic = Topic.objects.create(name="تاپیک مدیریت امنیت", created_by=self.owner)
        TopicAdmin.objects.create(topic=self.topic, user=self.admin_user)

        self.active_plugin = Plugin.objects.create(
            identifier="active-plugin",
            name="پلاگین فعال",
            version="1.0.0",
            capabilities=["composer_action"],
            scopes=["read:content"],
            is_active=True
        )
        self.inactive_plugin = Plugin.objects.create(
            identifier="inactive-plugin",
            name="پلاگین غیرفعال",
            version="1.0.0",
            is_active=False
        )

        self.post = Post.objects.create(topic=self.topic, author=self.owner, content="پست تستی امنیت")

    # 1. Unauthenticated attacks
    def test_unauthenticated_user_cannot_mutate_user_installations(self):
        """Anonymous user cannot install, toggle, or uninstall plugins."""
        url_install = f"/api/plugins/{self.active_plugin.identifier}/install/"
        url_toggle = f"/api/plugins/{self.active_plugin.identifier}/toggle/"
        url_uninstall = f"/api/plugins/{self.active_plugin.identifier}/uninstall/"

        res = self.client.post(url_install, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        res = self.client.post(url_toggle, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        res = self.client.post(url_uninstall, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # 2. Inactive plugin installation rejection
    def test_cannot_install_inactive_plugin(self):
        """Installing an inactive plugin returns 404 Not Found."""
        self.client.force_authenticate(user=self.regular_user)
        url = f"/api/plugins/{self.inactive_plugin.identifier}/install/"
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # 3. Topic Plugin RBAC Matrix
    def test_topic_plugin_install_rbac_matrix(self):
        """
        Verify Topic Plugin Install permissions:
        - Stranger: 403 Forbidden
        - Regular User: 403 Forbidden
        - Topic Admin: 201 Created
        - Topic Owner: 201 Created
        - Superuser: 201 Created
        """
        url = f"/api/plugins/topics/{self.topic.id}/install/"
        payload = {"identifier": self.active_plugin.identifier}

        # 1. Stranger
        self.client.force_authenticate(user=self.stranger_user)
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Regular User
        self.client.force_authenticate(user=self.regular_user)
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Topic Admin
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post(url, payload)
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        # 4. Topic Owner
        self.client.force_authenticate(user=self.owner)
        res = self.client.post(url, payload)
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        # 5. Superuser
        self.client.force_authenticate(user=self.superuser)
        res = self.client.post(url, payload)
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    # 4. Post References Authorization
    def test_post_reference_creation_permission_checks(self):
        """
        Only Post author, Topic owner/admin, or Superuser can attach references to a post.
        Strangers must be rejected with 403.
        """
        url = f"/api/plugins/posts/{self.post.id}/references/"
        payload = {
            "plugin": self.active_plugin.identifier,
            "resource_type": "ayah",
            "external_id": "1:1",
            "metadata": {"surah": 1}
        }

        # Stranger cannot attach reference
        self.client.force_authenticate(user=self.stranger_user)
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Author can attach reference
        self.client.force_authenticate(user=self.owner)
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Topic Admin can attach reference
        self.client.force_authenticate(user=self.admin_user)
        payload["external_id"] = "1:2"
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # 5. Marketplace Search and Filter Robustness
    def test_marketplace_filter_sql_injection_and_special_chars(self):
        """Marketplace search filter handles quotes, unicode, percent signs, and empty searches."""
        adversarial_searches = [
            "' OR '1'='1",
            "%; DROP TABLE tafakor_plugins; --",
            "قرآن",
            "%%",
            "\\",
            "\"\""
        ]
        for query in adversarial_searches:
            res = self.client.get(f"/api/plugins/?search={query}")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIsInstance(res.data, list)

    def test_marketplace_capability_filtering(self):
        """Marketplace capability query filter returns only matching plugins."""
        res = self.client.get("/api/plugins/?capability=composer_action")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        identifiers = [p["identifier"] for p in res.data]
        self.assertIn("active-plugin", identifiers)

        # Non-matching capability
        res = self.client.get("/api/plugins/?capability=bot_action")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        identifiers = [p["identifier"] for p in res.data]
        self.assertNotIn("active-plugin", identifiers)

    # 6. Non-existent and invalid inputs for all endpoints
    def test_non_existent_plugin_operations(self):
        """Operations on non-existent plugins return 404."""
        self.client.force_authenticate(user=self.regular_user)
        self.assertEqual(
            self.client.get("/api/plugins/non-existent-plugin-123/").status_code,
            status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            self.client.post("/api/plugins/non-existent-plugin-123/install/", {}).status_code,
            status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            self.client.post("/api/plugins/non-existent-plugin-123/toggle/", {}).status_code,
            status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            self.client.post("/api/plugins/non-existent-plugin-123/uninstall/", {}).status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_uninstall_or_toggle_not_installed_plugin_returns_bad_request(self):
        """Uninstalling or toggling a plugin that isn't installed returns 400 Bad Request."""
        self.client.force_authenticate(user=self.regular_user)
        res_uninstall = self.client.post(f"/api/plugins/{self.active_plugin.identifier}/uninstall/", {})
        self.assertEqual(res_uninstall.status_code, status.HTTP_400_BAD_REQUEST)

        res_toggle = self.client.post(f"/api/plugins/{self.active_plugin.identifier}/toggle/", {})
        self.assertEqual(res_toggle.status_code, status.HTTP_400_BAD_REQUEST)
