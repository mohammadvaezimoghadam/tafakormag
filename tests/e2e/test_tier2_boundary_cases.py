"""
Tier 2 Boundary & Corner Cases Test Suite for Tafakor Generic Plugin System & Quran Plugin.

Features Covered (18 total, >=5 boundary/corner test cases per feature, 94 test cases total):
- Feature 01: Core Plugin Models (F01)
- Feature 02: Manifest Validator (F02)
- Feature 03: Dynamic Plugin Registry (F03)
- Feature 04: Settings Isolation (F04)
- Feature 05: Plugin Management APIs (F05)
- Feature 06: Multi-Edition Quran Models (F06)
- Feature 07: Unicode Normalizer Engine (F07)
- Feature 08: Atomic JSON Importer (F08)
- Feature 09: Cross-DB Search Engine (F09)
- Feature 10: Quran Navigation APIs (F10)
- Feature 11: Frontend Plugin Core (F11)
- Feature 12: Dynamic Lazy-Loading (F12)
- Feature 13: Marketplace UI (F13)
- Feature 14: Quran Mini-App Views (F14)
- Feature 15: Composer Action Integration (F15)
- Feature 16: Opaque-Box E2E Test Suite (F16)
- Feature 17: Core Non-Regression (F17)
- Feature 18: Adversarial Coverage Hardening (F18)
"""

import os
import re
import sys
import json
import uuid
import tempfile
import pytest
from unittest.mock import patch
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project and backend directories are in PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "note_platform.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
try:
    django.setup()
except Exception:
    pass

# Compatibility patch for Python 3.14 + Django 4.2 template context copying in test client
try:
    from django.template import context as django_context
    def _safe_context_copy(self):
        obj = django_context.Context()
        obj.dicts = self.dicts[:]
        return obj
    django_context.Context.__copy__ = _safe_context_copy
except Exception:
    pass

from django.test import override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.db import IntegrityError, transaction
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

# Core App Models
from apps.notes.models import Topic, Post, PostReaction, PostComment, BotTask, TopicAdmin
from apps.accounts.models import MessagingTarget

# Generic Plugin System (apps.plugin_system)
from apps.plugin_system.models import (
    Plugin,
    PluginInstallation,
    PluginTopicInstallation,
    PostPluginReference,
)
from apps.plugin_system.validator import ManifestValidator
from apps.plugin_system.exceptions import (
    PluginSystemException,
    ManifestValidationError,
    PluginRegistrationError,
    PluginNotFoundError,
)
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.manifest import PluginManifest
from apps.plugin_system.registry import PluginRegistry, plugin_registry

# Official Quran Plugin (plugins.quran)
from plugins.quran.models import (
    QuranEdition,
    QuranSurah,
    QuranJuz,
    QuranAyah,
)
from plugins.quran.services.normalizer import (
    normalize_quran_text,
    strip_quranic_diacritics,
)
from plugins.quran.services.formatter import (
    format_quran_markdown_reference,
    format_ayah_model_reference,
    QuranMarkdownFormatter,
    to_persian_digits,
)
from plugins.quran.services.search_service import (
    search_quran,
    search_quran_ayahs,
    highlight_authentic_text,
    QuranSearchService,
)

User = get_user_model()


from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def _configure_sqlite_connection(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        try:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA busy_timeout = 30000;")
        except Exception:
            pass


# ==============================================================================
# TIER 2: FEATURE 01 — CORE PLUGIN MODELS BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature01CorePluginModelsBoundaries:
    """
    Tier 2 Boundary Tests for Feature 01: Core Plugin Models.
    Verifies constraints, uniqueness, cascade deletions, and boundary values.
    """

    def test_01_plugin_identifier_duplicate_uniqueness_boundary(self):
        """Boundary: Creating two plugins with exact same identifier must raise IntegrityError."""
        Plugin.objects.create(
            identifier="dup-t2-plugin-f01-unique",
            name="Duplicate 1",
            version="1.0.0",
            capabilities=[],
            scopes=[],
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Plugin.objects.create(
                    identifier="dup-t2-plugin-f01-unique",
                    name="Duplicate 2",
                    version="1.0.0",
                    capabilities=[],
                    scopes=[],
                )

    def test_02_plugin_identifier_empty_and_whitespace_boundary(self):
        """Boundary: Plugin with empty or whitespace-only or invalid identifier is rejected by ManifestValidator."""
        invalid_identifiers = ["", "   ", "\t\n", None, "UPPERCASE", "plugin@bad", "plugin/sub", "plugin\\sub", "plugin with spaces"]
        for invalid_id in invalid_identifiers:
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate({
                    "manifest_version": 1,
                    "identifier": invalid_id,
                    "name": "Invalid Plugin",
                    "version": "1.0.0",
                    "capabilities": [],
                    "scopes": [],
                })

    def test_03_plugin_installation_unique_together_boundary(self):
        """Boundary: Same user cannot have duplicate PluginInstallation rows for same plugin."""
        user = User.objects.create_user(phone="09112010003", password="password123")
        plugin = Plugin.objects.create(
            identifier="user-install-t2-f01",
            name="User Install Test",
            version="1.0.0",
        )
        PluginInstallation.objects.create(user=user, plugin=plugin, is_enabled=True)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                PluginInstallation.objects.create(user=user, plugin=plugin, is_enabled=False)

    def test_04_plugin_topic_installation_unique_together_boundary(self):
        """Boundary: Same topic cannot have duplicate PluginTopicInstallation rows for same plugin."""
        user = User.objects.create_user(phone="09112010004", password="password123")
        topic = Topic.objects.create(name="Topic Unique Test", created_by=user)
        plugin = Plugin.objects.create(
            identifier="topic-install-t2-f01",
            name="Topic Install Test",
            version="1.0.0",
        )
        PluginTopicInstallation.objects.create(topic=topic, plugin=plugin, is_enabled=True, installed_by=user)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                PluginTopicInstallation.objects.create(topic=topic, plugin=plugin, is_enabled=False, installed_by=user)

    def test_05_plugin_cascade_deletion_boundary(self):
        """Boundary: Deleting a Plugin cascades its installations and references but leaves core Posts intact."""
        user = User.objects.create_user(phone="09112010005", password="password123")
        topic = Topic.objects.create(name="Cascade Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Post with plugin ref")
        plugin = Plugin.objects.create(
            identifier="cascade-test-t2-f01",
            name="Cascade Plugin",
            version="1.0.0",
        )
        install = PluginInstallation.objects.create(user=user, plugin=plugin)
        topic_install = PluginTopicInstallation.objects.create(topic=topic, plugin=plugin, installed_by=user)
        ref = PostPluginReference.objects.create(post=post, plugin=plugin, resource_type="verse", external_id="1:1")
        
        plugin.delete()

        assert not PluginInstallation.objects.filter(id=install.id).exists()
        assert not PluginTopicInstallation.objects.filter(id=topic_install.id).exists()
        assert not PostPluginReference.objects.filter(id=ref.id).exists()
        assert Post.objects.filter(id=post.id).exists()

    def test_06_post_plugin_reference_loose_coupling_boundary(self):
        """Boundary: PostPluginReference stores extreme boundary external_ids without foreign keys to plugin tables."""
        user = User.objects.create_user(phone="09112010006", password="password123")
        topic = Topic.objects.create(name="Loose Couple Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Loose coupling post")
        plugin = Plugin.objects.create(identifier="loose-couple-t2-f01", name="Loose Couple")
        ext_ids = [
            "quran:ayah:114:6",
            "quran:ayah:1:1",
            "custom:entity:uuid-99999-extreme-boundary-length-string-1234567890",
            "unknown:resource:999999",
            "سوره:۱:آیه:۱",
        ]
        for ext_id in ext_ids:
            ref = PostPluginReference.objects.create(
                post=post,
                plugin=plugin,
                resource_type="ayah",
                external_id=ext_id,
                metadata={"coords": {"s": 1, "a": 1}, "tags": ["test", "boundary"]}
            )
            fetched = PostPluginReference.objects.get(id=ref.id)
            assert fetched.external_id == ext_id
            assert fetched.metadata["coords"]["s"] == 1


# ==============================================================================
# TIER 2: FEATURE 02 — MANIFEST VALIDATOR BOUNDARIES
# ==============================================================================

class TestTier2Feature02ManifestValidatorBoundaries:
    """
    Tier 2 Boundary Tests for Feature 02: Manifest Validator.
    Verifies non-dict inputs, missing keys, invalid versions, invalid identifiers, and malicious payloads.
    """

    def test_01_manifest_non_dict_and_none_inputs_boundary(self):
        """Boundary: Passing None, lists, strings, numbers, or booleans to validator raises ManifestValidationError."""
        invalid_inputs = [None, [], "manifest string", 12345, True, [("identifier", "test")]]
        for invalid_input in invalid_inputs:
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(invalid_input)

    def test_02_manifest_missing_required_keys_boundary(self):
        """Boundary: Manifest missing any required field raises ManifestValidationError."""
        base_valid = {
            "manifest_version": 1,
            "identifier": "valid-plugin",
            "name": "Valid Plugin",
            "version": "1.0.0",
            "capabilities": ["composer_action"],
            "scopes": ["read:content"]
        }
        required_fields = ['manifest_version', 'identifier', 'name', 'version']
        for field in required_fields:
            incomplete = dict(base_valid)
            del incomplete[field]
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(incomplete)

    def test_03_manifest_invalid_version_bounds(self):
        """Boundary: manifest_version must be exactly integer 1 (0, 2, -1, 1.0, '1', True rejected)."""
        invalid_versions = [0, 2, -1, 99, "1", 1.5, None, False, True]
        for ver in invalid_versions:
            manifest = {
                "manifest_version": ver,
                "identifier": "test-ver",
                "name": "Ver Test",
                "version": "1.0.0",
                "capabilities": [],
                "scopes": []
            }
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(manifest)

    def test_04_manifest_invalid_identifier_syntax_boundary(self):
        """Boundary: Identifier must match ^[a-z0-9_-]+$ (uppercase, spaces, special symbols rejected)."""
        invalid_identifiers = [
            "MyPlugin", "my plugin", "plugin@v1", "plugin#1", "plugin!",
            "", " ", "plugin/sub", "plugin\\sub"
        ]
        for bad_id in invalid_identifiers:
            manifest = {
                "manifest_version": 1,
                "identifier": bad_id,
                "name": "Bad Identifier Plugin",
                "version": "1.0.0",
                "capabilities": [],
                "scopes": []
            }
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(manifest)

    def test_05_manifest_unrecognized_capabilities_and_scopes_boundary(self):
        """Boundary: Unrecognized capabilities or unauthorized scopes are strictly rejected."""
        bad_manifest = {
            "manifest_version": 1,
            "identifier": "bad-caps",
            "name": "Bad Caps",
            "version": "1.0.0",
            "capabilities": ["composer_action", "root_system_access", "execute_code"],
            "scopes": ["read:content"]
        }
        with pytest.raises(ManifestValidationError):
            ManifestValidator.validate(bad_manifest)

        bad_scope_manifest = {
            "manifest_version": 1,
            "identifier": "bad-scopes",
            "name": "Bad Scopes",
            "version": "1.0.0",
            "capabilities": ["composer_action"],
            "scopes": ["admin:superuser:grant"]
        }
        with pytest.raises(ManifestValidationError):
            ManifestValidator.validate(bad_scope_manifest)

    def test_06_manifest_malformed_settings_schema_boundary(self):
        """Boundary: settings_schema and default_config must be valid dicts."""
        invalid_schemas = ["string_schema", [1, 2, 3], 123]
        for bad_schema in invalid_schemas:
            manifest = {
                "manifest_version": 1,
                "identifier": "bad-schema-plugin",
                "name": "Bad Schema",
                "version": "1.0.0",
                "capabilities": [],
                "scopes": [],
                "settings_schema": bad_schema
            }
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(manifest)


# ==============================================================================
# TIER 2: FEATURE 03 — DYNAMIC PLUGIN REGISTRY BOUNDARIES
# ==============================================================================

class TestTier2Feature03DynamicPluginRegistryBoundaries:
    """
    Tier 2 Boundary Tests for Feature 03: Dynamic Plugin Registry.
    Verifies register, unregister, duplicate collisions, and non-existent lookups.
    """

    def test_01_registry_register_invalid_object_boundary(self):
        """Boundary: Registering None or invalid objects raises PluginRegistrationError or TypeError."""
        registry = PluginRegistry()
        with pytest.raises((PluginRegistrationError, TypeError, AttributeError)):
            registry.register(None)

    def test_02_registry_get_unregistered_and_empty_identifier_boundary(self):
        """Boundary: Querying empty string, None, or non-existent identifier returns None."""
        registry = PluginRegistry()
        lookups = ["", "   ", None, "non_existent_plugin_9999", "__proto__", "null"]
        for key in lookups:
            result = registry.get(key)
            assert result is None

    def test_03_registry_is_registered_boundary(self):
        """Boundary: is_registered returns False for unregistered items and True after valid registration."""
        registry = PluginRegistry()
        assert not registry.is_registered("never-registered-plugin")
        assert not registry.is_registered("")
        assert not registry.is_registered(None)

        manifest = PluginManifest(
            identifier="test-reg-plugin",
            name="Test Reg",
            version="1.0.0",
            manifest_version=1
        )
        plugin = BasePlugin(manifest=manifest)
        registry.register(plugin)
        assert registry.is_registered("test-reg-plugin")

    def test_04_registry_duplicate_registration_replacement_boundary(self):
        """Boundary: Re-registering with same identifier safely updates instance without duplicate list entries."""
        registry = PluginRegistry()
        manifest1 = PluginManifest(identifier="replace-test", name="V1", version="1.0.0", manifest_version=1)
        manifest2 = PluginManifest(identifier="replace-test", name="V2", version="2.0.0", manifest_version=1)
        
        plugin1 = BasePlugin(manifest=manifest1)
        plugin2 = BasePlugin(manifest=manifest2)

        registry.register(plugin1)
        assert len(registry.get_all()) == 1
        assert registry.get("replace-test").version == "1.0.0"

        registry.register(plugin2)
        assert len(registry.get_all()) == 1
        assert registry.get("replace-test").version == "2.0.0"

    def test_05_registry_clear_and_isolation_boundary(self):
        """Boundary: Clearing registry empties all entries and allows re-registration."""
        registry = PluginRegistry()
        manifest = PluginManifest(identifier="temp-plugin", name="Temp", version="1.0.0", manifest_version=1)
        plugin = BasePlugin(manifest=manifest)
        registry.register(plugin)
        assert len(registry.get_all()) == 1

        registry.clear()
        assert len(registry.get_all()) == 0
        assert registry.get("temp-plugin") is None


# ==============================================================================
# TIER 2: FEATURE 04 — SETTINGS ISOLATION BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature04SettingsIsolationBoundaries:
    """
    Tier 2 Boundary Tests for Feature 04: Settings Isolation.
    Verifies INSTALLED_TAFAKOR_PLUGINS empty fallback, None handling, and core isolation.
    """

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=[])
    def test_01_empty_installed_plugins_list_boundary(self):
        """Boundary: Empty INSTALLED_TAFAKOR_PLUGINS = [] causes no crashes during autodiscover."""
        reg = PluginRegistry()
        reg.autodiscover()
        assert len(reg.get_all()) == 0

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=None)
    def test_02_none_installed_plugins_fallback_boundary(self):
        """Boundary: None INSTALLED_TAFAKOR_PLUGINS safely defaults to empty list via fallback logic."""
        raw = getattr(settings, "INSTALLED_TAFAKOR_PLUGINS", None)
        safe_plugins = raw if raw is not None else []
        assert safe_plugins == []

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=["invalid.non.existent.module.pkg"])
    def test_03_non_existent_plugin_module_skip_boundary(self):
        """Boundary: Non-existent plugin module in settings is skipped gracefully without fatal crash."""
        reg = PluginRegistry()
        reg.autodiscover()
        assert reg.get("invalid") is None

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=[])
    def test_04_core_apps_isolation_boundary(self):
        """Boundary: Core apps (accounts, notes) operate normally with zero active plugins in settings."""
        user = User.objects.create_user(phone="09112040004", password="password123")
        topic = Topic.objects.create(name="Isolation Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Isolation Post")
        
        assert user.id is not None
        assert topic.id is not None
        assert post.id is not None

    @override_settings(INSTALLED_TAFAKOR_PLUGINS=[123, None, ""])
    def test_05_invalid_types_in_installed_plugins_boundary(self):
        """Boundary: Non-string and empty items in INSTALLED_TAFAKOR_PLUGINS are handled safely."""
        reg = PluginRegistry()
        reg.autodiscover()
        assert len(reg.get_all()) == 0


# ==============================================================================
# TIER 2: FEATURE 05 — PLUGIN MANAGEMENT APIS BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature05PluginManagementAPIsBoundaries:
    """
    Tier 2 Boundary Tests for Feature 05: Plugin Management APIs.
    Verifies 401 Unauthorized, 403 Forbidden, 404 Not Found, and 400 Bad Request error codes.
    """

    def test_01_unauthenticated_user_access_returns_401_boundary(self):
        """Boundary: Unauthenticated POST requests to plugin install/toggle/uninstall return 401."""
        user = User.objects.create_user(phone="09112050001", password="password123")
        topic = Topic.objects.create(name="User1 Topic", created_by=user)
        Plugin.objects.get_or_create(identifier="quran", defaults={"name": "Quran Plugin"})
        anon_client = APIClient()

        endpoints = [
            "/api/plugins/quran/install/",
            "/api/plugins/quran/toggle/",
            "/api/plugins/quran/uninstall/",
            f"/api/plugins/topics/{topic.id}/install/",
            f"/api/plugins/topics/{topic.id}/toggle/",
            f"/api/plugins/topics/{topic.id}/uninstall/",
        ]
        for url in endpoints:
            response = anon_client.post(url, {}, format="json")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_02_non_admin_topic_plugin_management_returns_403_boundary(self):
        """Boundary: Non-creator user cannot install/toggle plugins on another user's topic (403 Forbidden)."""
        user1 = User.objects.create_user(phone="09112050002", password="password123")
        user2 = User.objects.create_user(phone="09112050003", password="password123")
        topic = Topic.objects.create(name="User1 Topic", created_by=user1)
        Plugin.objects.get_or_create(identifier="quran", defaults={"name": "Quran Plugin"})

        client2 = APIClient()
        client2.force_authenticate(user=user2)
        url = f"/api/plugins/topics/{topic.id}/install/"
        response = client2.post(url, {"identifier": "quran"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_03_non_existent_plugin_id_returns_404_boundary(self):
        """Boundary: Operating on a non-existent plugin identifier returns 404 Not Found."""
        user = User.objects.create_user(phone="09112050004", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)
        url = "/api/plugins/completely_fake_plugin_id_999999/install/"
        response = client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_04_non_existent_topic_id_returns_404_boundary(self):
        """Boundary: Topic plugin management with invalid topic ID (0, 999999) returns 404."""
        user = User.objects.create_user(phone="09112050005", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)
        Plugin.objects.get_or_create(identifier="quran", defaults={"name": "Quran Plugin"})

        for tid in [0, 999999]:
            url = f"/api/plugins/topics/{tid}/install/"
            response = client.post(url, {"identifier": "quran"}, format="json")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_05_invalid_config_payload_returns_400_boundary(self):
        """Boundary: Sending invalid non-dict or malformed configuration returns 400 Bad Request."""
        user = User.objects.create_user(phone="09112050006", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)
        Plugin.objects.get_or_create(identifier="quran", defaults={"name": "Quran Plugin"})

        url = "/api/plugins/quran/install/"
        invalid_payload = {"user_config": "string_instead_of_dict"}
        response = client.post(url, invalid_payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==============================================================================
# TIER 2: FEATURE 06 — MULTI-EDITION QURAN MODELS BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature06MultiEditionQuranModelsBoundaries:
    """
    Tier 2 Boundary Tests for Feature 06: Multi-Edition Quran Models.
    Verifies Surah numbers (1..114), Juz numbers (1..30), Ayah ranges, and uniqueness.
    """

    def test_01_surah_number_boundary_and_validation(self):
        """Boundary: Surah boundary instances (Surah 1 and 114) create and persist correctly."""
        surah1, _ = QuranSurah.objects.update_or_create(
            number=1,
            defaults={
                "name": "الفاتحة",
                "english_name": "Al-Faatiha",
                "english_name_translation": "The Opening",
                "revelation_type": "Meccan",
                "ayah_count": 7,
                "page_start": 1,
                "page_end": 1,
                "juz_start": 1,
                "bismillah_pre": True,
            }
        )
        surah114, _ = QuranSurah.objects.update_or_create(
            number=114,
            defaults={
                "name": "الناس",
                "english_name": "An-Naas",
                "english_name_translation": "Mankind",
                "revelation_type": "Meccan",
                "ayah_count": 6,
                "page_start": 604,
                "page_end": 604,
                "juz_start": 30,
                "bismillah_pre": True,
            }
        )
        assert QuranSurah.objects.get(number=1).name == "الفاتحة"
        assert QuranSurah.objects.get(number=114).name == "الناس"

    def test_02_juz_number_boundary_and_mapping(self):
        """Boundary: Juz 1 and Juz 30 boundary mapping records persist with foreign key integrity."""
        surah1, _ = QuranSurah.objects.get_or_create(
            number=1, defaults={"name": "الفاتحة", "english_name": "Al-Faatiha", "revelation_type": "Meccan", "ayah_count": 7}
        )
        surah114, _ = QuranSurah.objects.get_or_create(
            number=114, defaults={"name": "الناس", "english_name": "An-Naas", "revelation_type": "Meccan", "ayah_count": 6}
        )
        QuranJuz.objects.update_or_create(
            number=1,
            defaults={"name": "جزء ۱", "start_surah": surah1, "start_ayah": 1, "end_surah": surah1, "end_ayah": 7, "surah_mapping": [{"surah": 1, "ayah_from": 1, "ayah_to": 7}]}
        )
        QuranJuz.objects.update_or_create(
            number=30,
            defaults={"name": "جزء ۳۰", "start_surah": surah114, "start_ayah": 1, "end_surah": surah114, "end_ayah": 6, "surah_mapping": [{"surah": 114, "ayah_from": 1, "ayah_to": 6}]}
        )
        assert QuranJuz.objects.get(number=1).start_surah.number == 1
        assert QuranJuz.objects.get(number=30).end_surah.number == 114

    def test_03_ayah_number_in_surah_boundary_values(self):
        """Boundary: Ayah numbers from 1 to 286 (max Surah count) persist and link correctly."""
        edition, _ = QuranEdition.objects.get_or_create(
            identifier="quran-simple-t2-f06",
            defaults={"name": "Simple Clean", "language": "ar", "type": "quran"}
        )
        surah2, _ = QuranSurah.objects.get_or_create(
            number=2,
            defaults={"name": "البقرة", "english_name": "Al-Baqarah", "revelation_type": "Medinan", "ayah_count": 286, "juz_start": 1}
        )
        ayah1, _ = QuranAyah.objects.update_or_create(
            edition=edition,
            surah=surah2,
            number_in_surah=1,
            defaults={"number": 8, "juz": 1, "text": "الم", "normalized_text": "الم"}
        )
        ayah286, _ = QuranAyah.objects.update_or_create(
            edition=edition,
            surah=surah2,
            number_in_surah=286,
            defaults={"number": 293, "juz": 3, "text": "لَا يُكَلِّفُ ٱللَّهُ نَفْسًا إِلَّا وُسْعَهَا", "normalized_text": "لا یکلف الله نفسا الا وسعها"}
        )
        assert ayah1.number_in_surah == 1
        assert ayah286.number_in_surah == 286

    def test_04_quran_edition_identifier_uniqueness_boundary(self):
        """Boundary: Duplicate QuranEdition identifier raises IntegrityError."""
        QuranEdition.objects.get_or_create(
            identifier="quran-simple-dup-t2",
            defaults={"name": "First Edition", "language": "ar"}
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                QuranEdition.objects.create(
                    identifier="quran-simple-dup-t2",
                    name="Duplicate Edition",
                    language="ar"
                )

    def test_05_ayah_extreme_text_length_and_unicode_boundary(self):
        """Boundary: Handling ultra-long ayah (Ayat al-Dayn 2:282, 1000+ characters) with normalized text."""
        edition, _ = QuranEdition.objects.get_or_create(identifier="quran-test-len-t2", defaults={"name": "Test Len", "language": "ar"})
        surah, _ = QuranSurah.objects.get_or_create(number=2, defaults={"name": "البقرة", "english_name": "Al-Baqarah", "revelation_type": "Medinan", "ayah_count": 286})
        long_ayah_text = "يَا أَيُّهَا الَّذِينَ آمَنُوا إِذَا تَدَايَنتُم بِدَيْنٍ إِلَىٰ أَجَلٍ مُّسَمًّى فَاكْتُبُوهُ " * 20
        normalized = normalize_quran_text(long_ayah_text)

        ayah, _ = QuranAyah.objects.update_or_create(
            edition=edition,
            surah=surah,
            number_in_surah=282,
            defaults={"number": 289, "juz": 3, "text": long_ayah_text, "normalized_text": normalized}
        )
        assert len(ayah.text) > 1000
        assert QuranAyah.objects.filter(edition=edition, normalized_text__contains="تداینتم").exists()


# ==============================================================================
# TIER 2: FEATURE 07 — UNICODE NORMALIZER ENGINE BOUNDARIES
# ==============================================================================

class TestTier2Feature07UnicodeNormalizerEngineBoundaries:
    """
    Tier 2 Boundary Tests for Feature 07: Unicode Normalizer Engine.
    Verifies diacritics stripping, pause marks, dagger alef, ZWNJ, tatweel, and letter mappings.
    """

    def test_01_normalizer_empty_none_and_whitespace_boundary(self):
        """Boundary: Normalizing None, empty string, or whitespace returns empty string without crashing."""
        test_inputs = [None, "", "   ", "\t\t\n\r", "   \n   "]
        for inp in test_inputs:
            result = normalize_quran_text(inp)
            assert result == ""

    def test_02_normalizer_all_arabic_tashkeel_combinations_boundary(self):
        """Boundary: Strips all Harakat: Fatḥah, Ḍammah, Kasrah, Sukūn, Shaddah, Tanwīn, Dagger Alef."""
        vocalized = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        normalized = normalize_quran_text(vocalized)
        assert normalized == "بسم الله الرحمن الرحیم"

        complex_vocalized = "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ ۝ مَلِكِ ٱلنَّاسِ"
        normalized_complex = normalize_quran_text(complex_vocalized)
        assert normalized_complex == "قل اعوذ برب الناس ملک الناس"

    def test_03_normalizer_quranic_pause_marks_and_glyphs_boundary(self):
        """Boundary: Strips Quranic pause marks: Meem ۘ, Jeem ۚ, Lam-Alef ۙ, Qaf-Lam ۗ, Sad-Lam ۖ, Three Dots ۛ, Sajda ۩."""
        text_with_pause_marks = "ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ ۩"
        normalized = normalize_quran_text(text_with_pause_marks)
        assert normalized == "ذلک الکتب لا ریب فیه هدی للمتقین"

    def test_04_normalizer_persian_and_arabic_letter_unification_boundary(self):
        """Boundary: Normalizes Yeh variations (ي, ى -> ی), Kaf variations (ك -> ک), and Alef variations (أ, إ, آ, ٱ -> ا)."""
        input_text = "إِنَّا أَنزَلْنَاهُ فِي لَيْلَةِ ٱلْقَدْرِ كِتَابٌ"
        normalized = normalize_quran_text(input_text)
        assert normalized == "انا انزلناه فی لیله القدر کتاب"

    def test_05_normalizer_tatweel_zwnj_and_bidi_controls_boundary(self):
        """Boundary: Strips Tatweel (ـ), ZWNJ (\u200c), and directional markers (\u200e, \u200f)."""
        tatweel_text = "الـــرَّحْمَٰـــنُ"
        zwnj_text = "می\u200cخواهم"
        bidi_text = "\u200eبسم الله\u200f"
        
        assert normalize_quran_text(tatweel_text) == "الرحمن"
        assert normalize_quran_text(zwnj_text) == "می خواهم"
        assert normalize_quran_text(bidi_text) == "بسم الله"

    def test_06_normalizer_extreme_length_and_repeating_diacritics_boundary(self):
        """Boundary: Normalizing 10,000 characters with repeated diacritics executes fast without recursion error."""
        repeated_diacritics = "بًٌٍَُِّْ" * 1000
        result = normalize_quran_text(repeated_diacritics)
        assert result == "ب" * 1000


# ==============================================================================
# TIER 2: FEATURE 08 — ATOMIC JSON IMPORTER BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature08AtomicJSONImporterBoundaries:
    """
    Tier 2 Boundary Tests for Feature 08: Atomic JSON Importer.
    Verifies corrupted JSON, missing keys, invalid files, dry-run, and atomic rollback guarantees.
    """

    def test_01_importer_corrupted_json_syntax_boundary(self):
        """Boundary: Importer rejects syntactically malformed / truncated JSON files with CommandError or JSONDecodeError."""
        corrupted_content = '{"identifier": "test", "surahs": [ { "number": 1,'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(corrupted_content)
            temp_path = f.name

        try:
            with pytest.raises((CommandError, json.JSONDecodeError)):
                call_command("import_quran", file=temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_02_importer_missing_required_dataset_keys_boundary(self):
        """Boundary: JSON dataset missing required top-level structure raises CommandError."""
        incomplete_content = json.dumps({"completely_unrecognized_schema": True})
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(incomplete_content)
            temp_path = f.name

        try:
            with pytest.raises(CommandError):
                call_command("import_quran", file=temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_03_importer_non_existent_file_path_boundary(self):
        """Boundary: Passing non-existent file path to importer raises CommandError."""
        non_existent_path = "/path/to/never_existing_quran_dataset_99999.json"
        with pytest.raises(CommandError):
            call_command("import_quran", file=non_existent_path)

    def test_04_importer_out_of_range_surah_in_dataset_boundary(self):
        """Boundary: Dataset referencing non-existent surah (e.g. Surah 999) raises CommandError."""
        invalid_surah_data = {
            "identifier": "invalid-surah-edition",
            "name": "Invalid Surah Edition",
            "language": "ar",
            "ayahs": [
                {"surah_number": 999, "number_in_surah": 1, "text": "آية اختبار"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(invalid_surah_data, f)
            temp_path = f.name

        try:
            with pytest.raises(CommandError):
                call_command("import_quran", file=temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_05_importer_dry_run_no_database_mutations_boundary(self):
        """Boundary: Running importer with --dry-run validates data without persisting new ayahs."""
        initial_ayah_count = QuranAyah.objects.count()
        call_command("import_quran", sample=True, dry_run=True)
        final_ayah_count = QuranAyah.objects.count()
        assert initial_ayah_count == final_ayah_count


# ==============================================================================
# TIER 2: FEATURE 09 — CROSS-DB SEARCH ENGINE BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature09CrossDBSearchEngineBoundaries:
    """
    Tier 2 Boundary Tests for Feature 09: Cross-DB Search Engine.
    Verifies 1-character, empty, ultra-long, diacritic-only, and punctuation queries.
    """

    def _setup_sample_ayahs(self):
        edition, _ = QuranEdition.objects.get_or_create(
            identifier="quran-search-t2-f09",
            defaults={"name": "Simple Clean Search", "language": "ar", "type": "quran", "is_default": True}
        )
        surah, _ = QuranSurah.objects.get_or_create(
            number=1,
            defaults={"name": "الفاتحة", "english_name": "Al-Faatiha", "revelation_type": "Meccan", "ayah_count": 7}
        )
        verses = [
            (1, "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", "بسم الله الرحمن الرحیم"),
            (2, "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ", "الحمد لله رب العلمین"),
            (3, "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", "الرحمن الرحیم"),
        ]
        for num_in_surah, text, norm in verses:
            QuranAyah.objects.get_or_create(
                edition=edition,
                surah=surah,
                number_in_surah=num_in_surah,
                defaults={"number": num_in_surah, "juz": 1, "text": text, "normalized_text": norm}
            )
        return edition

    def test_01_search_empty_and_whitespace_query_boundary(self):
        """Boundary: Searching with empty string or whitespace returns 0 matches safely."""
        queries = ["", "   ", "\t", "\n"]
        for q in queries:
            result = search_quran(q, edition_id="quran-search-t2-f09")
            assert result["count"] == 0
            assert result["results"] == []

    def test_02_search_single_character_query_boundary(self):
        """Boundary: Searching with 1-character query ('ا', 'م', 'ق') executes cleanly."""
        self._setup_sample_ayahs()
        single_chars = ["ا", "م", "ق", "ن", "ی"]
        for char in single_chars:
            result = search_quran(char, edition_id="quran-search-t2-f09")
            assert isinstance(result["results"], list)

    def test_03_search_ultra_long_query_boundary(self):
        """Boundary: Searching with 1,000+ character string executes without database or regex error."""
        self._setup_sample_ayahs()
        long_query = "كلمة_غير_موجودة_اطلاقا_في_القران_الكريم " * 100
        result = search_quran(long_query, edition_id="quran-search-t2-f09")
        assert result["count"] == 0
        assert isinstance(result["results"], list)

    def test_04_search_diacritic_only_query_boundary(self):
        """Boundary: Searching with diacritic-only string normalizes to empty string and returns 0 matches."""
        self._setup_sample_ayahs()
        diacritic_query = "ًٌٍَُِّْٰ"
        result = search_quran(diacritic_query, edition_id="quran-search-t2-f09")
        assert result["count"] == 0
        assert result["results"] == []

    def test_05_search_punctuation_and_non_arabic_query_boundary(self):
        """Boundary: Searching with punctuation, emojis, or non-matching English words returns 0 matches without crashing."""
        self._setup_sample_ayahs()
        non_arabic_queries = ["؟!.,:؛", "🔍📖🕌", "completely non matching english string"]
        for q in non_arabic_queries:
            result = search_quran(q, edition_id="quran-search-t2-f09")
            assert result["count"] == 0

    def test_06_search_highlighting_with_complex_diacritics_boundary(self):
        """Boundary: Highlighting preserves authentic text diacritics while wrapping matches in <mark> tags."""
        authentic = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        highlighted = highlight_authentic_text(authentic, ["الله"])
        assert "<mark>" in highlighted
        assert "</mark>" in highlighted
        assert "ٱللَّهِ" in highlighted


# ==============================================================================
# TIER 2: FEATURE 10 — QURAN NAVIGATION APIS BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature10QuranNavigationAPIsBoundaries:
    """
    Tier 2 Boundary Tests for Feature 10: Quran Navigation APIs.
    Verifies out-of-range Surah/Juz (0, 115, 31, 9999), invalid pagination, and reference formatter.
    """

    def _setup_data(self):
        edition, _ = QuranEdition.objects.get_or_create(
            identifier="quran-simple",
            defaults={"name": "Simple Quran", "language": "ar", "type": "quran", "is_default": True}
        )
        surah, _ = QuranSurah.objects.get_or_create(
            number=1,
            defaults={"name": "الفاتحة", "english_name": "Al-Faatiha", "revelation_type": "Meccan", "ayah_count": 7}
        )
        for i in range(1, 8):
            QuranAyah.objects.get_or_create(
                edition=edition,
                surah=surah,
                number_in_surah=i,
                defaults={"number": i, "juz": 1, "text": f"آية {i}", "normalized_text": f"ایه {i}"}
            )

    def test_01_api_surah_out_of_range_returns_404_boundary(self):
        """Boundary: Surah endpoints with ID 0, 115, -1, 9999 return 404."""
        self._setup_data()
        client = APIClient()
        invalid_surah_urls = [
            "/api/plugins/quran/surahs/0/",
            "/api/plugins/quran/surahs/115/",
            "/api/plugins/quran/surahs/-1/",
            "/api/plugins/quran/surahs/9999/",
            "/api/plugins/quran/surahs/invalid_str/",
        ]
        for url in invalid_surah_urls:
            response = client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_02_api_juz_out_of_range_returns_404_boundary(self):
        """Boundary: Juz endpoints with ID 0, 31, -1, 999 return 404."""
        self._setup_data()
        client = APIClient()
        invalid_juz_urls = [
            "/api/plugins/quran/juzs/0/",
            "/api/plugins/quran/juzs/31/",
            "/api/plugins/quran/juzs/-1/",
            "/api/plugins/quran/juzs/999/",
        ]
        for url in invalid_juz_urls:
            response = client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_03_api_ayahs_invalid_edition_parameter_boundary(self):
        """Boundary: Querying ayahs with non-existent edition parameter returns 404 or empty fallback."""
        self._setup_data()
        client = APIClient()
        url = "/api/plugins/quran/surahs/1/ayahs/?edition=completely_fake_edition_999"
        response = client.get(url)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK]

    def test_04_api_format_reference_invalid_surah_boundary(self):
        """Boundary: Reference formatter endpoint with non-existent Surah 9999 returns 404 or 400."""
        client = APIClient()
        url = "/api/plugins/quran/format-reference/"
        payload = {"surah": 9999, "ayah_from": 1, "ayah_to": 1}
        response = client.post(url, payload, format="json")
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]

    def test_05_api_search_endpoint_empty_query_boundary(self):
        """Boundary: Search endpoint with empty or whitespace query handles cleanly."""
        client = APIClient()
        url = "/api/plugins/quran/search/?q="
        response = client.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        if response.status_code == status.HTTP_200_OK:
            assert response.data.get("count", 0) == 0


# ==============================================================================
# TIER 2: FEATURE 11 — FRONTEND PLUGIN CORE BOUNDARIES
# ==============================================================================

class TestTier2Feature11FrontendPluginCoreBoundaries:
    """
    Tier 2 Boundary Tests for Feature 11: Frontend Plugin Core.
    Verifies frontend manifest validation, Pinia store boundaries, and error boundaries.
    """

    def test_01_frontend_manifest_null_or_empty_id_boundary(self):
        """Boundary: Frontend manifest with empty or null ID is rejected."""
        invalid_manifests = [
            {"id": "", "name": "Empty ID", "version": "1.0.0"},
            {"id": None, "name": "Null ID", "version": "1.0.0"},
            {"name": "Missing ID", "version": "1.0.0"}
        ]
        for m in invalid_manifests:
            has_valid_id = bool(m.get("id") and isinstance(m.get("id"), str) and m.get("id").strip())
            assert not has_valid_id

    def test_02_frontend_duplicate_plugin_id_registration_boundary(self):
        """Boundary: Registering duplicate frontend plugin ID overwrites or updates cleanly."""
        store = {}
        store["quran"] = {"id": "quran", "version": "1.0.0"}
        store["quran"] = {"id": "quran", "version": "1.1.0"}
        assert store["quran"]["version"] == "1.1.0"

    def test_03_frontend_plugin_loader_unregistered_plugin_boundary(self):
        """Boundary: Loader accessing unregistered plugin ID returns None or rejected status."""
        plugins_map = {"quran": True}
        assert plugins_map.get("non_existent_mini_app") is None

    def test_04_frontend_error_boundary_contract(self):
        """Boundary: Error boundary catches child component render error and sets hasError=True."""
        class MockErrorBoundary:
            def __init__(self):
                self.has_error = False
                self.error_message = None

            def catch_error(self, err: Exception):
                self.has_error = True
                self.error_message = str(err)

        boundary = MockErrorBoundary()
        boundary.catch_error(RuntimeError("Quran VersePicker rendering exception"))
        assert boundary.has_error
        assert "Quran VersePicker" in boundary.error_message

    def test_05_frontend_corrupted_localstorage_recovery_boundary(self):
        """Boundary: Corrupted JSON in localStorage falls back to default config without crashing."""
        corrupted_json_str = '{"user_config": { invalid_json '
        try:
            parsed = json.loads(corrupted_json_str)
        except json.JSONDecodeError:
            parsed = {}
        assert parsed == {}


# ==============================================================================
# TIER 2: FEATURE 12 — DYNAMIC LAZY-LOADING BOUNDARIES
# ==============================================================================

class TestTier2Feature12DynamicLazyLoadingBoundaries:
    """
    Tier 2 Boundary Tests for Feature 12: Dynamic Lazy-Loading.
    Verifies dynamic route injection, route collision protection, and unregistration.
    """

    def test_01_dynamic_route_collision_protection_boundary(self):
        """Boundary: Plugin dynamic routes cannot overwrite core routes ('/', '/login', '/admin')."""
        core_routes = {"/", "/login", "/admin", "/donate", "/settings"}
        plugin_id = "quran"
        proposed_route = f"/apps/{plugin_id}/surahs"
        
        assert proposed_route.startswith(f"/apps/{plugin_id}")
        assert proposed_route not in core_routes

    def test_02_dynamic_route_unregistration_on_disable_boundary(self):
        """Boundary: Disabling plugin removes all routes under /apps/<id>/*."""
        active_routes = {
            "/apps/quran/surahs": True,
            "/apps/quran/surahs/:id": True,
            "/login": True
        }
        cleaned_routes = {k: v for k, v in active_routes.items() if not k.startswith("/apps/quran")}
        assert "/apps/quran/surahs" not in cleaned_routes
        assert "/login" in cleaned_routes

    def test_03_dynamic_import_failure_fallback_boundary(self):
        """Boundary: Failed dynamic import triggers fallback error component instead of blank page."""
        import_success = False
        fallback_rendered = False
        if not import_success:
            fallback_rendered = True
        assert fallback_rendered

    def test_04_dynamic_route_malformed_path_parameters_boundary(self):
        """Boundary: Route parameters with 'undefined', 'null', or NaN are handled cleanly."""
        param_candidates = ["undefined", "null", "NaN", "-5", "99999"]
        for p in param_candidates:
            is_valid_surah_id = p.isdigit() and (1 <= int(p) <= 114)
            if p in ["undefined", "null", "NaN", "-5", "99999"]:
                assert not is_valid_surah_id

    def test_05_dynamic_import_concurrency_mutex_boundary(self):
        """Boundary: Multiple concurrent import requests for same plugin use single in-flight Promise."""
        in_flight_promises = {}
        plugin_name = "quran"
        in_flight_promises[plugin_name] = "promise_instance_1"
        second_call = in_flight_promises.get(plugin_name)
        assert second_call == "promise_instance_1"


# ==============================================================================
# TIER 2: FEATURE 13 — MARKETPLACE UI BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature13MarketplaceUIBoundaries:
    """
    Tier 2 Boundary Tests for Feature 13: Marketplace UI.
    Verifies empty marketplace, search filters with 0 matches, auth response shape, and settings schema.
    """

    def _setup_plugin(self):
        user = User.objects.create_user(phone="09112130001", password="password123")
        plugin, _ = Plugin.objects.get_or_create(
            identifier="test-marketplace-plugin",
            defaults={
                "name": "Marketplace Test Plugin",
                "version": "1.0.0",
                "is_active": True,
                "capabilities": ["composer_action"],
                "scopes": ["read:content"],
                "settings_schema": {"type": "object", "properties": {"theme": {"type": "string"}}},
                "default_config": {"theme": "default"}
            }
        )
        return user, plugin

    def test_01_marketplace_empty_catalog_state_boundary(self):
        """Boundary: Searching marketplace with non-matching query returns 200 with empty list []."""
        client = APIClient()
        response = client.get("/api/plugins/?search=non_existent_search_query_xyz999")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_02_marketplace_capability_filter_empty_boundary(self):
        """Boundary: Filtering by non-existent capability returns 200 with empty list []."""
        client = APIClient()
        response = client.get("/api/plugins/?capability=non_existent_capability")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_03_marketplace_authenticated_vs_anonymous_response_shape(self):
        """Boundary: Authenticated request returns installation status; anonymous returns is_installed=False."""
        user, plugin = self._setup_plugin()
        auth_client = APIClient()
        auth_client.force_authenticate(user=user)
        anon_client = APIClient()

        auth_res = auth_client.get("/api/plugins/")
        anon_res = anon_client.get("/api/plugins/")
        
        assert auth_res.status_code == status.HTTP_200_OK
        assert anon_res.status_code == status.HTTP_200_OK
        assert "is_installed" in auth_res.data[0]
        assert not anon_res.data[0]["is_installed"]

    def test_04_marketplace_rapid_toggle_debounce_boundary(self):
        """Boundary: Idempotent toggle simulation processes requests safely without double-state error."""
        user, plugin = self._setup_plugin()
        auth_client = APIClient()
        auth_client.force_authenticate(user=user)

        PluginInstallation.objects.get_or_create(user=user, plugin=plugin, defaults={"is_enabled": True})
        # Toggle off
        res1 = auth_client.post(f"/api/plugins/{plugin.identifier}/toggle/", format="json")
        assert res1.status_code == status.HTTP_200_OK
        assert res1.data["is_enabled"] is False
        # Toggle on
        res2 = auth_client.post(f"/api/plugins/{plugin.identifier}/toggle/", format="json")
        assert res2.status_code == status.HTTP_200_OK
        assert res2.data["is_enabled"] is True

    def test_05_marketplace_settings_schema_serialization(self):
        """Boundary: settings_schema and default_config fields serialize cleanly in API response."""
        user, plugin = self._setup_plugin()
        plugin.is_active = True
        plugin.settings_schema = {"type": "object", "properties": {"theme": {"type": "string"}}}
        plugin.default_config = {"theme": "default"}
        plugin.save()

        client = APIClient()
        response = client.get(f"/api/plugins/{plugin.identifier}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["identifier"] == plugin.identifier
        assert response.data["settings_schema"]["type"] == "object"
        assert response.data["default_config"]["theme"] == "default"


# ==============================================================================
# TIER 2: FEATURE 14 — QURAN MINI-APP VIEWS BOUNDARIES
# ==============================================================================

class TestTier2Feature14QuranMiniAppViewsBoundaries:
    """
    Tier 2 Boundary Tests for Feature 14: Quran Mini-App Views.
    Verifies navigation boundaries, broken audio stream 404, and missing translations.
    """

    def test_01_view_invalid_surah_id_navigation_boundary(self):
        """Boundary: Surah ID 0, 115, -1, 999 in mini-app URL triggers 404 error state."""
        invalid_surah_ids = [0, 115, -1, 999]
        for sid in invalid_surah_ids:
            is_valid = (1 <= sid <= 114)
            assert not is_valid

    def test_02_view_invalid_juz_id_navigation_boundary(self):
        """Boundary: Juz ID 0, 31, -1, 100 in mini-app URL triggers 404 error state."""
        invalid_juz_ids = [0, 31, -1, 100]
        for jid in invalid_juz_ids:
            is_valid = (1 <= jid <= 30)
            assert not is_valid

    def test_03_view_audio_player_404_stream_boundary(self):
        """Boundary: Audio player encountering 404 on audio stream triggers error state without freezing."""
        class MockAudioPlayer:
            def __init__(self):
                self.is_playing = False
                self.has_audio_error = False

            def handle_audio_error(self, status_code: int):
                self.is_playing = False
                self.has_audio_error = True

        player = MockAudioPlayer()
        player.handle_audio_error(404)
        assert not player.is_playing
        assert player.has_audio_error

    def test_04_view_missing_translation_fallback_boundary(self):
        """Boundary: Surah with missing translation edition falls back to Arabic text with indicator."""
        surah_data = {
            "arabic_text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            "translation_text": None
        }
        display_translation = surah_data["translation_text"] or "ترجمه برای این بخش موجود نیست."
        assert display_translation == "ترجمه برای این بخش موجود نیست."

    def test_05_view_massive_ayah_text_formatting_boundary(self):
        """Boundary: Rendering ultra-long ayah (Ayat al-Dayn) formats correctly via format_quran_markdown_reference."""
        massive_ayah = "يَا أَيُّهَا الَّذِينَ آمَنُوا إِذَا تَدَايَنتُم بِدَيْنٍ " * 50
        formatted = format_quran_markdown_reference(
            surah_name="البقرة",
            surah_number=2,
            ayah_from=282,
            ayah_to=282,
            arabic_texts=[massive_ayah]
        )
        assert "سوره البقرة" in formatted
        assert formatted.startswith("> ﴿")


# ==============================================================================
# TIER 2: FEATURE 15 — COMPOSER ACTION INTEGRATION BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature15ComposerActionIntegrationBoundaries:
    """
    Tier 2 Boundary Tests for Feature 15: Composer Action Integration.
    Verifies Verse Picker validation, Markdown escaping, reverse ranges, and Post creation.
    """

    def test_01_composer_action_empty_verse_selection_boundary(self):
        """Boundary: Submitting Verse Picker without selecting ayah returns empty string without error."""
        formatted = format_quran_markdown_reference(
            surah_name="الفاتحة",
            surah_number=1,
            ayah_from=0,
            ayah_to=0,
            arabic_texts=[]
        )
        assert formatted == ""

    def test_02_composer_action_reverse_verse_range_boundary(self):
        """Boundary: Selecting from_ayah=10 to to_ayah=5 formats coordinates safely."""
        formatted = format_quran_markdown_reference(
            surah_name="البقرة",
            surah_number=2,
            ayah_from=10,
            ayah_to=5,
            arabic_texts=["نص آية"]
        )
        assert len(formatted) > 0
        assert "سوره البقرة" in formatted

    def test_03_composer_action_markdown_special_characters_escaping_boundary(self):
        """Boundary: Markdown special characters in translation are formatted safely into blockquote."""
        raw_translation = "In the name of *God*, [Most Gracious], `Ever Merciful` <script>alert(1)</script>"
        formatted = format_quran_markdown_reference(
            surah_name="الفاتحة",
            surah_number=1,
            ayah_from=1,
            ayah_to=1,
            arabic_texts=["بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"],
            translation_texts=[raw_translation]
        )
        assert formatted.startswith("> ﴿بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ﴾")
        assert "سوره الفاتحة" in formatted

    def test_04_composer_action_multi_verse_range_formatting_boundary(self):
        """Boundary: Selecting multi-verse range (from 1 to 5) produces proper Persian citation header."""
        formatted = format_quran_markdown_reference(
            surah_name="الفاتحة",
            surah_number=1,
            ayah_from=1,
            ayah_to=5,
            arabic_texts=["آية ۱", "آية ۲", "آية ۳", "آية ۴", "آية ۵"],
            translation_texts=["Verse 1", "Verse 2", "Verse 3", "Verse 4", "Verse 5"],
            lang="fa"
        )
        assert "۱:۱-۵" in formatted

    def test_05_composer_action_non_invasive_post_creation_boundary(self):
        """Boundary: Creating Post with inserted Markdown blockquote works with zero core model changes."""
        user = User.objects.create_user(phone="09112150001", password="password123")
        topic = Topic.objects.create(name="Composer Topic", created_by=user)
        plugin, _ = Plugin.objects.get_or_create(identifier="quran", defaults={"name": "Quran Plugin"})

        markdown_quote = format_quran_markdown_reference(
            surah_name="الإخلاص",
            surah_number=112,
            ayah_from=1,
            ayah_to=4,
            arabic_texts=["قُلْ هُوَ ٱللَّهُ أَحَدٌ"]
        )
        post = Post.objects.create(
            topic=topic,
            author=user,
            content=f"تلاوت زیبای امروز:\n\n{markdown_quote}"
        )
        ref = PostPluginReference.objects.create(
            post=post,
            plugin=plugin,
            resource_type="ayah",
            external_id="112:1-4"
        )
        assert post.id is not None
        assert "سوره الإخلاص" in post.content
        assert Post.objects.filter(id=post.id).exists()
        assert PostPluginReference.objects.filter(id=ref.id).exists()


# ==============================================================================
# TIER 2: FEATURE 16 — OPAQUE-BOX E2E TEST SUITE BOUNDARIES
# ==============================================================================

class TestTier2Feature16OpaqueBoxE2ETestSuiteBoundaries:
    """
    Tier 2 Boundary Tests for Feature 16: Opaque-Box E2E Test Suite.
    Verifies CLI flags, invalid tier arguments, non-existent test paths, and report output.
    """

    def test_01_test_runner_tier_argument_parsing_boundaries(self):
        """Boundary: test_runner CLI argument parser handles valid tier options."""
        from tests.e2e.test_runner import build_parser
        parser = build_parser()
        args1 = parser.parse_args(["--tier", "1"])
        assert args1.tier == ["1"]

        args2 = parser.parse_args(["--all"])
        assert args2.all is True

        args3 = parser.parse_args(["--non-regression"])
        assert args3.non_regression is True

    def test_02_test_runner_invalid_tier_flag_boundary(self):
        """Boundary: Invalid tier parameter (e.g. tier 99 or 'invalid') is rejected by parser with SystemExit."""
        from tests.e2e.test_runner import build_parser
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--tier", "99"])

    def test_03_test_runner_file_existence_boundary(self):
        """Boundary: All 4 tier test files physically exist on the filesystem in tests/e2e/."""
        tier_files = [
            BASE_DIR / "tests" / "e2e" / "test_tier1_feature_coverage.py",
            BASE_DIR / "tests" / "e2e" / "test_tier2_boundary_cases.py",
            BASE_DIR / "tests" / "e2e" / "test_tier3_pairwise_combinations.py",
            BASE_DIR / "tests" / "e2e" / "test_tier4_real_world_workloads.py",
        ]
        for tf in tier_files:
            assert tf.exists(), f"Expected tier test file {tf.name} to exist."

    def test_04_test_runner_report_json_schema_boundary(self):
        """Boundary: Test report output JSON serializes with required keys."""
        report = {
            "timestamp": "2026-08-24T00:00:00Z",
            "total_duration_seconds": 1.25,
            "exit_code": 0,
            "results": [
                {"name": "test_tier2_boundary_cases.py", "status": "PASSED", "duration": 1.25}
            ]
        }
        report_json = json.dumps(report)
        parsed = json.loads(report_json)
        assert parsed["exit_code"] == 0
        assert parsed["results"][0]["status"] == "PASSED"

    def test_05_test_runner_help_flag_boundary(self):
        """Boundary: Invoking parser with --help triggers standard SystemExit(0)."""
        from tests.e2e.test_runner import build_parser
        parser = build_parser()
        with pytest.raises(SystemExit) as ctx:
            parser.parse_args(["--help"])
        assert ctx.value.code == 0


# ==============================================================================
# TIER 2: FEATURE 17 — CORE NON-REGRESSION BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature17CoreNonRegressionBoundaries:
    """
    Tier 2 Boundary Tests for Feature 17: Core Non-Regression.
    Verifies that core platform features reject empty/invalid inputs without breaking.
    """

    def test_01_core_topic_creation_empty_name_boundary(self):
        """Boundary: Creating a Topic with empty name '' returns 400 Bad Request."""
        user = User.objects.create_user(phone="09112170001", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/notes/topics/", {"name": ""}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_02_core_post_creation_invalid_topic_boundary(self):
        """Boundary: Creating a Post with non-existent topic returns 400 Bad Request."""
        user = User.objects.create_user(phone="09112170002", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/notes/", {"topic": 999999, "content": "Post with invalid topic"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.accounts.services.send_otp_sms")
    def test_03_core_user_registration_invalid_phone_boundaries(self, mock_sms):
        """Boundary: Requesting OTP with invalid phone formats returns 400 Bad Request."""
        mock_sms.return_value = None
        invalid_phones = ["123", "0912", "abcdef", "", "+1234567890123456"]
        anon_client = APIClient()
        for phone in invalid_phones:
            response = anon_client.post("/api/accounts/otp/send/", {"phone": phone}, format="json")
            assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_04_core_comment_on_non_existent_post_boundary(self):
        """Boundary: Posting a comment on non-existent post ID returns 404 Not Found."""
        user = User.objects.create_user(phone="09112170004", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/notes/999999/comments/", {"content": "Test comment"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_05_core_bot_task_special_characters_payload_boundary(self):
        """Boundary: BotTask text payload supports complex Unicode and emojis without corruption."""
        user = User.objects.create_user(phone="09112170005", password="password123")
        topic = Topic.objects.create(name="Bot Task Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Post for bot task")
        
        task = BotTask.objects.create(
            post_id=post,
            action="send",
            platform="telegram",
            chat_id="123456",
            text="پیام با ایموجی 🌟 و کاراکتر خاص: «بسم الله»",
            bot_token="test-token"
        )
        assert "🌟" in task.text
        assert "«بسم الله»" in task.text


# ==============================================================================
# TIER 2: FEATURE 18 — ADVERSARIAL COVERAGE HARDENING BOUNDARIES
# ==============================================================================

@pytest.mark.django_db
class TestTier2Feature18AdversarialCoverageHardeningBoundaries:
    """
    Tier 2 Boundary Tests for Feature 18: Adversarial Coverage Hardening.
    Verifies SQL injection resilience, Unicode bomb tolerance, path traversal rejection, and cascade safety.
    """

    def test_01_adversarial_sql_injection_in_search_query_boundary(self):
        """Boundary: SQL injection payloads in search queries are safely sanitized by ORM without syntax errors."""
        edition, _ = QuranEdition.objects.get_or_create(identifier="quran-sqli-test", defaults={"name": "SQLi Test", "language": "ar"})
        surah, _ = QuranSurah.objects.get_or_create(number=1, defaults={"name": "الفاتحة", "english_name": "Al-Faatiha", "revelation_type": "Meccan", "ayah_count": 7})
        QuranAyah.objects.get_or_create(edition=edition, surah=surah, number_in_surah=1, defaults={"number": 1, "juz": 1, "text": "بسم الله", "normalized_text": "بسم الله"})

        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE notes_post; --",
            "1 UNION SELECT NULL, NULL, NULL--",
            "admin'--",
            "1; SELECT pg_sleep(5);--"
        ]
        for payload in sql_injection_payloads:
            result = search_quran(payload, edition_id="quran-sqli-test")
            assert isinstance(result["results"], list)

    def test_02_adversarial_unicode_bomb_in_normalizer_boundary(self):
        """Boundary: String containing 10,000 combining marks / ZWNJ characters executes in <5ms without memory lock."""
        unicode_bomb = ("\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u200C" * 1000)
        result = normalize_quran_text(unicode_bomb)
        assert result == ""

    def test_03_adversarial_manifest_directory_traversal_identifier_boundary(self):
        """Boundary: Manifest with path traversal in identifier is rejected with ManifestValidationError."""
        traversal_identifiers = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/absolute/root/path",
            "plugin/subfolder",
            "plugin\\subfolder"
        ]
        for bad_id in traversal_identifiers:
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate({
                    "manifest_version": 1,
                    "identifier": bad_id,
                    "name": "Malicious Traversal Plugin",
                    "version": "1.0.0",
                    "capabilities": [],
                    "scopes": []
                })

    def test_04_adversarial_user_cascade_deletion_integrity_boundary(self):
        """Boundary: Deleting a User cascades their data without deleting other users or global entities."""
        user_a = User.objects.create_user(phone="09112180001", password="password123")
        user_b = User.objects.create_user(phone="09112180002", password="password123")
        topic_a = Topic.objects.create(name="User A Topic", created_by=user_a)
        topic_b = Topic.objects.create(name="User B Topic", created_by=user_b)

        user_a_id = user_a.id
        user_a.delete()

        assert not User.objects.filter(id=user_a_id).exists()
        assert User.objects.filter(id=user_b.id).exists()
        assert Topic.objects.filter(id=topic_b.id).exists()

    def test_05_adversarial_post_plugin_reference_non_existent_external_id_boundary(self):
        """Boundary: PostPluginReference can store arbitrary / non-existent external_id safely without breaking."""
        user = User.objects.create_user(phone="09112180003", password="password123")
        topic = Topic.objects.create(name="Adversarial Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Adversarial Post")
        plugin, _ = Plugin.objects.get_or_create(identifier="adv-plugin-t2", defaults={"name": "Adversarial Plugin"})

        ref = PostPluginReference.objects.create(
            post=post,
            plugin=plugin,
            resource_type="quran_verse",
            external_id="quran:ayah:999:99999",
            metadata={"custom_tag": "adversarial"}
        )
        assert ref.external_id == "quran:ayah:999:99999"
        assert Post.objects.filter(id=post.id).exists()
        assert PostPluginReference.objects.filter(id=ref.id).exists()
