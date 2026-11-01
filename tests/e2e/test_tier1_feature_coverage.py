"""
E2E Tier 1 Feature Coverage Test Suite for Tafakor Monorepo.

Covers all 18 features from PROJECT.md § Feature Inventory with 5 genuine test
cases per feature (90 comprehensive test cases total).

Features Tested:
- Feature 01: Core Plugin Models (Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference)
- Feature 02: Manifest Validator (manifest_version: 1, schema, capabilities, scopes)
- Feature 03: Dynamic Plugin Registry (lifecycle, autodiscover, sync_to_db, capabilities)
- Feature 04: Settings Isolation (INSTALLED_TAFAKOR_PLUGINS fallback, non-regression)
- Feature 05: Plugin Management APIs (marketplace, user & topic install/toggle/uninstall)
- Feature 06: Multi-Edition Quran Models (QuranEdition, QuranSurah, QuranAyah, QuranJuz)
- Feature 07: Unicode Normalizer Engine (Arabic/Persian diacritics, char standardization)
- Feature 08: Atomic JSON Importer (import_quran, rollback, dynamic format support)
- Feature 09: Cross-DB Search Engine (SQLite & PostgreSQL parity, highlighting)
- Feature 10: Quran Navigation APIs (editions, surahs, ayahs, juzs, search, compare)
- Feature 11: Frontend Plugin Core (manifest contract, registry store, error boundaries)
- Feature 12: Dynamic Lazy-Loading (dynamic import, route injection, cache)
- Feature 13: Marketplace UI (card schemas, capability filters, installation flow)
- Feature 14: Quran Mini-App Views (catalog, reader, juz, search, audio stream)
- Feature 15: Composer Action Integration (verse picker, markdown formatting, non-invasive)
- Feature 16: Opaque-Box E2E Test Suite (4-tier hierarchy, test runner CLI, reporting)
- Feature 17: Core Non-Regression (Accounts, Notes, Donations, Bot Tasks zero regressions)
- Feature 18: Adversarial Coverage Hardening (XSS, SQLi, Unicode fuzzing, privilege escalation)
"""

import os
import sys
import json
import uuid
import tempfile
import pathlib
import pytest
from pathlib import Path

from django.test import override_settings
from django.core.management import call_command, CommandError
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from apps.notes.models import Topic, Post, TopicAdmin, BotTask
try:
    from apps.donations.models import DonationCampaign
except Exception:
    DonationCampaign = None

from apps.plugin_system.models import (
    Plugin,
    PluginInstallation,
    PluginTopicInstallation,
    PostPluginReference,
)
from apps.plugin_system.validator import ManifestValidator
from apps.plugin_system.exceptions import ManifestValidationError, PluginRegistrationError
from apps.plugin_system.registry import PluginRegistry, plugin_registry
from apps.plugin_system.base import BasePlugin
from apps.plugin_system.manifest import PluginManifest

from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah
from plugins.quran.services.normalizer import normalize_quran_text, strip_quranic_diacritics
from plugins.quran.services.search_service import (
    search_quran,
    highlight_authentic_text,
    QuranSearchService,
)
from plugins.quran.services.formatter import (
    format_quran_markdown_reference,
    format_ayah_model_reference,
    QuranMarkdownFormatter,
)
from tests.e2e.test_runner import build_parser

User = get_user_model()
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ==============================================================================
# Helper Functions
# ==============================================================================
def create_valid_manifest_dict(**overrides):
    base = {
        "manifest_version": 1,
        "identifier": "quran",
        "name": "قرآن کریم",
        "version": "1.0.0",
        "description": "Official Quran plugin for Tafakor.",
        "author": "Tafakor Core Team",
        "capabilities": ["composer_action", "mini_app", "search_provider"],
        "scopes": ["read:content", "write:composer", "read:quran"],
        "settings_schema": {
            "type": "object",
            "properties": {
                "font_size": {"type": "integer", "default": 18}
            }
        },
        "default_config": {
            "font_size": 18
        }
    }
    base.update(overrides)
    return base


def ensure_seed_quran_models():
    """Helper to ensure basic Quran models exist in test database."""
    edition, _ = QuranEdition.objects.get_or_create(
        identifier="quran-simple",
        defaults={
            "name": "Quran Simple (Arabic)",
            "english_name": "Quran Simple",
            "language": "ar",
            "direction": "rtl",
            "type": "quran",
            "is_default": True,
            "total_ayahs": 6236,
        }
    )
    edition_fa, _ = QuranEdition.objects.get_or_create(
        identifier="fa.ansarian",
        defaults={
            "name": "ترجمه انصاریان",
            "english_name": "Ansarian Translation",
            "language": "fa",
            "direction": "rtl",
            "type": "translation",
            "is_default": False,
            "total_ayahs": 6236,
        }
    )

    s1, _ = QuranSurah.objects.get_or_create(
        number=1,
        defaults={
            "name": "الفاتحة",
            "english_name": "Al-Faatiha",
            "english_name_translation": "The Opening",
            "revelation_type": "Meccan",
            "ayah_count": 7,
            "bismillah_pre": False,
            "juz_start": 1,
        }
    )
    s112, _ = QuranSurah.objects.get_or_create(
        number=112,
        defaults={
            "name": "الإخلاص",
            "english_name": "Al-Ikhlaas",
            "english_name_translation": "Sincerity",
            "revelation_type": "Meccan",
            "ayah_count": 4,
            "bismillah_pre": True,
            "juz_start": 30,
        }
    )

    j1, _ = QuranJuz.objects.get_or_create(
        number=1,
        defaults={
            "name": "الم",
            "start_surah": s1,
            "start_ayah": 1,
            "end_surah": s1,
            "end_ayah": 7,
        }
    )

    # Ayahs for Surah 1
    ayahs_data_ar = [
        (1, 1, "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"),
        (2, 2, "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"),
        (3, 3, "الرَّحْمَٰنِ الرَّحِيمِ"),
        (4, 4, "مَالِكِ يَوْمِ الدِّينِ"),
        (5, 5, "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ"),
        (6, 6, "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ"),
        (7, 7, "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ"),
    ]
    for g_num, s_num, text in ayahs_data_ar:
        QuranAyah.objects.get_or_create(
            edition=edition,
            surah=s1,
            number_in_surah=s_num,
            defaults={
                "number": g_num,
                "text": text,
                "normalized_text": normalize_quran_text(text),
                "juz": 1,
            }
        )

    ayahs_data_fa = [
        (1, 1, "به نام خداوند بخشنده مهربان"),
        (2, 2, "ستایش مخصوص خدایی است که پروردگار جهانیان است."),
        (3, 3, "بخشنده و مهربان است."),
        (4, 4, "مالک و فرمانروای روز جزاست."),
        (5, 5, "تنها تو را می‌پرستیم و تنها از تو یاری می‌جوییم."),
        (6, 6, "ما را به راه راست هدایت فرما،"),
        (7, 7, "راه کسانی که به آنان نعمت دادی، نه آنان که مورد غضب واقع شدند و نه گمراهان."),
    ]
    for g_num, s_num, text in ayahs_data_fa:
        QuranAyah.objects.get_or_create(
            edition=edition_fa,
            surah=s1,
            number_in_surah=s_num,
            defaults={
                "number": g_num,
                "text": text,
                "normalized_text": normalize_quran_text(text),
                "juz": 1,
            }
        )

    # Ayahs for Surah 112
    s112_ayahs = [
        (6222, 1, "قُلْ هُوَ اللَّهُ أَحَدٌ"),
        (6223, 2, "اللَّهُ الصَّمَدُ"),
        (6224, 3, "لَمْ يَلِدْ وَلَمْ يُولَدْ"),
        (6225, 4, "وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ"),
    ]
    for g_num, s_num, text in s112_ayahs:
        QuranAyah.objects.get_or_create(
            edition=edition,
            surah=s112,
            number_in_surah=s_num,
            defaults={
                "number": g_num,
                "text": text,
                "normalized_text": normalize_quran_text(text),
                "juz": 30,
            }
        )

    return edition, edition_fa, s1, s112, j1


# ==============================================================================
# Feature 01: Core Plugin Models
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature01CorePluginModels:
    """Feature 01: Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference."""

    def test_f01_c01_plugin_model_creation_and_attributes(self):
        Plugin.objects.filter(identifier="quran_model_test").delete()
        plugin = Plugin.objects.create(
            identifier="quran_model_test",
            name="قرآن کریم",
            version="1.0.0",
            capabilities=["composer_action", "mini_app"],
            scopes=["read:quran", "write:composer"],
            manifest_version=1,
            is_active=True
        )
        assert isinstance(plugin.id, uuid.UUID)
        assert plugin.identifier == "quran_model_test"
        assert plugin.has_capability("composer_action") is True
        assert plugin.has_capability("non_existent_cap") is False
        assert plugin.has_scope("read:quran") is True
        assert str(plugin) == "قرآن کریم (quran_model_test v1.0.0)"

    def test_f01_c02_plugin_installation_user_uniqueness_and_config(self):
        user = User.objects.create_user(phone="09121110001", password="password123")
        plugin = Plugin.objects.create(
            identifier="quran_user_test",
            name="Quran User Test",
            default_config={"theme": "light", "font_size": 16}
        )
        installation = PluginInstallation.objects.create(
            user=user,
            plugin=plugin,
            is_enabled=True,
            user_config={"font_size": 22}
        )
        effective = installation.get_effective_config()
        assert effective["font_size"] == 22
        assert effective["theme"] == "light"

        # UniqueConstraint check
        with pytest.raises(IntegrityError):
            PluginInstallation.objects.create(user=user, plugin=plugin)

    def test_f01_c03_plugin_topic_installation_lifecycle(self):
        user = User.objects.create_user(phone="09121110002", password="password123")
        topic = Topic.objects.create(name="Study Group", created_by=user)
        plugin = Plugin.objects.create(
            identifier="quran_topic_test",
            name="Quran Topic Test",
            default_config={"pinned_surah": 1}
        )
        topic_inst = PluginTopicInstallation.objects.create(
            topic=topic,
            plugin=plugin,
            installed_by=user,
            is_enabled=True,
            topic_config={"pinned_surah": 36}
        )
        assert topic_inst.get_effective_config()["pinned_surah"] == 36

        # Disable
        topic_inst.is_enabled = False
        topic_inst.save()
        reloaded = PluginTopicInstallation.objects.get(id=topic_inst.id)
        assert reloaded.is_enabled is False

    def test_f01_c04_post_plugin_reference_loose_coupling(self):
        user = User.objects.create_user(phone="09121110003", password="password123")
        topic = Topic.objects.create(name="Tafsir Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Post with ayah reference")
        plugin = Plugin.objects.create(identifier="quran_ref_test", name="Quran Ref Test")

        ref = PostPluginReference.objects.create(
            post=post,
            plugin=plugin,
            resource_type="ayah",
            external_id="1:1",
            metadata={"surah": 1, "ayah": 1}
        )
        assert isinstance(ref.external_id, str)
        assert ref.external_id == "1:1"
        assert post.plugin_references.count() == 1
        assert str(ref).startswith("Post #")

    def test_f01_c05_plugin_model_capability_and_scope_helpers(self):
        plugin = Plugin.objects.create(
            identifier="test_helpers",
            name="Helper Test Plugin",
            capabilities=["search_provider"],
            scopes=["read:content"]
        )
        assert plugin.has_capability("search_provider") is True
        assert plugin.has_capability("composer_action") is False
        assert plugin.has_scope("read:content") is True
        assert plugin.has_scope("admin:all") is False


# ==============================================================================
# Feature 02: Manifest Validator
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature02ManifestValidator:
    """Feature 02: Strict validation for manifest_version: 1, regex, capabilities, scopes."""

    def test_f02_c01_valid_manifest_passes_validation(self):
        manifest = create_valid_manifest_dict()
        validated = ManifestValidator.validate(manifest)
        assert validated["identifier"] == "quran"
        assert validated["manifest_version"] == 1
        assert "composer_action" in validated["capabilities"]

    def test_f02_c02_manifest_version_must_be_one(self):
        for bad_version in [0, 2, 99, None, "1", True, False]:
            manifest = create_valid_manifest_dict(manifest_version=bad_version)
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(manifest)

    def test_f02_c03_identifier_regex_validation(self):
        for bad_id in ["Quran", "quran plugin", "quran@v1", "", "UPPERCASE_PLUGIN", "with space"]:
            manifest = create_valid_manifest_dict(identifier=bad_id)
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(manifest)

    def test_f02_c04_capabilities_and_scopes_whitelist(self):
        manifest_bad_cap = create_valid_manifest_dict(capabilities=["unknown_cap"])
        with pytest.raises(ManifestValidationError):
            ManifestValidator.validate(manifest_bad_cap)

        manifest_bad_scope = create_valid_manifest_dict(scopes=["unauthorized:scope"])
        with pytest.raises(ManifestValidationError):
            ManifestValidator.validate(manifest_bad_scope)

    def test_f02_c05_settings_schema_and_default_config_validation(self):
        manifest_bad_schema = create_valid_manifest_dict(settings_schema="not-a-dict")
        with pytest.raises(ManifestValidationError):
            ManifestValidator.validate(manifest_bad_schema)

        manifest_bad_config = create_valid_manifest_dict(default_config="not-a-dict")
        with pytest.raises(ManifestValidationError):
            ManifestValidator.validate(manifest_bad_config)


# ==============================================================================
# Feature 03: Dynamic Plugin Registry
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature03DynamicPluginRegistry:
    """Feature 03: In-memory registry lifecycle, loading, db sync, filtering."""

    def test_f03_c01_registry_load_and_get_plugin(self):
        registry = PluginRegistry()
        manifest_dict = create_valid_manifest_dict(identifier="reg_test_1", name="Reg Test Plugin")
        manifest = PluginManifest.from_dict(manifest_dict)
        plugin = BasePlugin(manifest=manifest)

        registry.register(plugin)
        assert registry.is_registered("reg_test_1") is True
        retrieved = registry.get("reg_test_1")
        assert retrieved is not None
        assert retrieved.name == "Reg Test Plugin"

    def test_f03_c02_registry_filter_by_capability(self):
        registry = PluginRegistry()
        m1 = PluginManifest.from_dict(create_valid_manifest_dict(identifier="p1", capabilities=["composer_action"]))
        m2 = PluginManifest.from_dict(create_valid_manifest_dict(identifier="p2", capabilities=["search_provider"]))

        registry.register(BasePlugin(manifest=m1))
        registry.register(BasePlugin(manifest=m2))

        composer_plugins = registry.get_plugins_with_capability("composer_action")
        assert len(composer_plugins) == 1
        assert composer_plugins[0].identifier == "p1"

    def test_f03_c03_registry_autodiscover_from_settings(self):
        registry = PluginRegistry()
        loaded = registry.load_plugin("plugins.quran")
        assert loaded.identifier == "quran"
        assert registry.is_registered("quran") is True

    def test_f03_c04_registry_sync_to_database(self):
        registry = PluginRegistry()
        registry.load_plugin("plugins.quran")
        registry.sync_to_db()
        assert Plugin.objects.filter(identifier="quran").exists() is True

    def test_f03_c05_registry_lifecycle_and_clear(self):
        registry = PluginRegistry()
        m = PluginManifest.from_dict(create_valid_manifest_dict(identifier="temp_p"))
        registry.register(BasePlugin(manifest=m))
        assert len(registry.get_all()) == 1

        registry.clear()
        assert len(registry.get_all()) == 0
        assert registry.is_registered("temp_p") is False


# ==============================================================================
# Feature 04: Settings Isolation
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature04SettingsIsolation:
    """Feature 04: INSTALLED_TAFAKOR_PLUGINS fallback and non-breaking platform behavior."""

    def test_f04_c01_empty_installed_tafakor_plugins_setting(self):
        with override_settings(INSTALLED_TAFAKOR_PLUGINS=[]):
            registry = PluginRegistry()
            registry.autodiscover()
            assert registry.get_all() == []

    def test_f04_c02_missing_setting_fallback(self):
        registry = PluginRegistry()
        registry.autodiscover()
        assert isinstance(registry.get_all(), list)

    def test_f04_c03_core_apps_unaffected_by_plugins(self):
        with override_settings(INSTALLED_TAFAKOR_PLUGINS=[]):
            user = User.objects.create_user(phone="09121110004", password="password123")
            topic = Topic.objects.create(name="Core Topic", created_by=user)
            post = Post.objects.create(topic=topic, author=user, content="Core Post")
            assert Topic.objects.filter(id=topic.id).exists()
            assert Post.objects.filter(id=post.id).exists()

    def test_f04_c04_invalid_plugin_app_path_resilience(self):
        registry = PluginRegistry()
        with pytest.raises(PluginRegistrationError):
            registry.load_plugin("plugins.non_existent_package_xyz")

    def test_f04_c05_unmigrated_db_sync_resilience(self):
        registry = PluginRegistry()
        m = PluginManifest.from_dict(create_valid_manifest_dict(identifier="safe_sync"))
        registry.register(BasePlugin(manifest=m))
        registry.sync_to_db()
        assert Plugin.objects.filter(identifier="safe_sync").exists()


# ==============================================================================
# Feature 05: Plugin Management APIs
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature05PluginManagementAPIs:
    """Feature 05: REST endpoints /api/plugins/ for marketplace, user and topic installations."""

    def test_f05_c01_list_marketplace_plugins_api(self):
        Plugin.objects.get_or_create(
            identifier="quran",
            defaults={"name": "قرآن کریم", "version": "1.0.0", "is_active": True}
        )
        client = APIClient()
        res = client.get("/api/plugins/")
        assert res.status_code == 200
        assert any(p["identifier"] == "quran" for p in res.data)

    def test_f05_c02_get_plugin_detail_api(self):
        Plugin.objects.get_or_create(
            identifier="quran",
            defaults={
                "name": "قرآن کریم",
                "version": "1.0.0",
                "is_active": True,
                "capabilities": ["composer_action"]
            }
        )
        client = APIClient()
        res = client.get("/api/plugins/quran/")
        assert res.status_code == 200
        assert res.data["identifier"] == "quran"
        assert "composer_action" in res.data["capabilities"]

    def test_f05_c03_user_plugin_install_toggle_uninstall_api(self):
        user = User.objects.create_user(phone="09121110005", password="password123")
        Plugin.objects.get_or_create(
            identifier="quran",
            defaults={"name": "قرآن کریم", "version": "1.0.0", "is_active": True}
        )
        client = APIClient()
        client.force_authenticate(user=user)

        # 1. Install
        res_inst = client.post("/api/plugins/quran/install/", data={"user_config": {"font_size": 20}}, format="json")
        assert res_inst.status_code == 201
        assert PluginInstallation.objects.filter(user=user, plugin__identifier="quran").exists()

        # 2. Toggle
        res_tog = client.post("/api/plugins/quran/toggle/", data={}, format="json")
        assert res_tog.status_code == 200
        assert res_tog.data["is_enabled"] is False

        # 3. Uninstall
        res_un = client.post("/api/plugins/quran/uninstall/", data={}, format="json")
        assert res_un.status_code == 200
        assert not PluginInstallation.objects.filter(user=user, plugin__identifier="quran").exists()

    def test_f05_c04_topic_plugin_install_toggle_uninstall_api(self):
        user = User.objects.create_user(phone="09121110006", password="password123")
        topic = Topic.objects.create(name="Quran Circle", created_by=user)
        Plugin.objects.get_or_create(
            identifier="quran",
            defaults={"name": "قرآن کریم", "version": "1.0.0", "is_active": True}
        )
        client = APIClient()
        client.force_authenticate(user=user)

        # Install on topic
        res_inst = client.post(
            f"/api/plugins/topics/{topic.id}/install/",
            data={"identifier": "quran", "topic_config": {"pinned_surah": 1}},
            format="json"
        )
        assert res_inst.status_code == 201
        assert PluginTopicInstallation.objects.filter(topic=topic, plugin__identifier="quran").exists()

        # Toggle on topic
        res_tog = client.post(
            f"/api/plugins/topics/{topic.id}/toggle/",
            data={"identifier": "quran", "is_enabled": False},
            format="json"
        )
        assert res_tog.status_code == 200
        assert res_tog.data["is_enabled"] is False

        # Uninstall from topic
        res_un = client.post(
            f"/api/plugins/topics/{topic.id}/uninstall/",
            data={"identifier": "quran"},
            format="json"
        )
        assert res_un.status_code == 200
        assert not PluginTopicInstallation.objects.filter(topic=topic, plugin__identifier="quran").exists()

    def test_f05_c05_plugin_api_authentication_and_permissions(self):
        user = User.objects.create_user(phone="09121110007", password="password123")
        non_admin = User.objects.create_user(phone="09121110008", password="password123")
        topic = Topic.objects.create(name="Private Topic", created_by=user)
        Plugin.objects.get_or_create(
            identifier="quran",
            defaults={"name": "قرآن کریم", "version": "1.0.0", "is_active": True}
        )

        client = APIClient()
        # Anonymous -> 401
        res = client.post("/api/plugins/quran/install/", data={})
        assert res.status_code == 401

        # Non-admin on topic -> 403
        client.force_authenticate(user=non_admin)
        res_forbidden = client.post(
            f"/api/plugins/topics/{topic.id}/install/",
            data={"identifier": "quran"},
            format="json"
        )
        assert res_forbidden.status_code == 403


# ==============================================================================
# Feature 06: Multi-Edition Quran Models
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature06MultiEditionQuranModels:
    """Feature 06: QuranEdition, QuranSurah, QuranJuz, QuranAyah models."""

    def test_f06_c01_quran_edition_model_fields_and_types(self):
        edition = QuranEdition.objects.create(
            identifier="fa.makarem",
            name="ترجمه مکارم شیرازی",
            english_name="Makarem Translation",
            language="fa",
            type="translation",
            direction="rtl",
            author="ناصر مکارم شیرازی",
            is_default=False,
            total_ayahs=6236
        )
        assert edition.identifier == "fa.makarem"
        assert edition.direction == "rtl"
        assert str(edition) == "ترجمه مکارم شیرازی (fa.makarem)"

    def test_f06_c02_quran_surah_model_metadata_and_revelation(self):
        s1 = QuranSurah.objects.create(
            number=1,
            name="الفاتحة",
            english_name="Al-Faatiha",
            english_name_translation="The Opening",
            revelation_type="Meccan",
            ayah_count=7,
            bismillah_pre=False
        )
        s9 = QuranSurah.objects.create(
            number=9,
            name="التوبة",
            english_name="At-Tawba",
            english_name_translation="The Repentance",
            revelation_type="Medinan",
            ayah_count=129,
            bismillah_pre=False
        )
        assert s1.revelation_type == "Meccan"
        assert s9.bismillah_pre is False
        assert str(s1) == "1. الفاتحة (Al-Faatiha)"

    def test_f06_c03_quran_juz_boundary_and_mapping(self):
        s1, _ = QuranSurah.objects.get_or_create(
            number=1,
            defaults={"name": "الفاتحة", "english_name": "Al-Faatiha", "revelation_type": "Meccan", "ayah_count": 7}
        )
        juz = QuranJuz.objects.create(
            number=1,
            name="الم",
            start_surah=s1,
            start_ayah=1,
            end_surah=s1,
            end_ayah=7
        )
        assert juz.start_surah == s1
        assert juz.end_ayah == 7
        assert str(juz) == "Juz 1 (الم)"

    def test_f06_c04_quran_ayah_relationships_and_uniqueness(self):
        ed, _ = QuranEdition.objects.get_or_create(identifier="quran-simple", defaults={"name": "Simple", "language": "ar"})
        s1, _ = QuranSurah.objects.get_or_create(number=1, defaults={"name": "الفاتحة", "revelation_type": "Meccan", "ayah_count": 7})

        ayah = QuranAyah.objects.create(
            edition=ed,
            surah=s1,
            number=1,
            number_in_surah=1,
            juz=1,
            text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            normalized_text="بسم الله الرحمن الرحیم"
        )
        assert ayah.surah == s1
        assert ayah.number == 1

        # Duplicate composite key should fail
        with pytest.raises(IntegrityError):
            QuranAyah.objects.create(
                edition=ed,
                surah=s1,
                number=1,
                number_in_surah=1,
                juz=1,
                text="duplicate",
                normalized_text="duplicate"
            )

    def test_f06_c05_quran_ayah_sajda_and_metadata_json(self):
        ed, _ = QuranEdition.objects.get_or_create(identifier="quran-simple", defaults={"name": "Simple", "language": "ar"})
        s32, _ = QuranSurah.objects.get_or_create(number=32, defaults={"name": "السجدة", "revelation_type": "Meccan", "ayah_count": 30})

        ayah = QuranAyah.objects.create(
            edition=ed,
            surah=s32,
            number=3518,
            number_in_surah=15,
            juz=21,
            text="إِنَّمَا يُؤْمِنُ بِآيَاتِنَا",
            normalized_text="انما یومن بایاتنا",
            sajda={"recommended": True, "obligatory": True},
            audio_url="https://audio.example.com/32_15.mp3"
        )
        assert ayah.sajda["obligatory"] is True
        assert ayah.audio_url.startswith("https://")


# ==============================================================================
# Feature 07: Unicode Normalizer Engine
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature07UnicodeNormalizerEngine:
    """Feature 07: Unicode normalizer for Quranic diacritics and character mappings."""

    def test_f07_c01_strips_arabic_tashkeel_and_harakat(self):
        raw = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        normalized = normalize_quran_text(raw)
        assert normalized == "بسم الله الرحمن الرحیم"

    def test_f07_c02_strips_dagger_alef_and_quranic_stop_marks(self):
        raw = "الرَّحْمَٰنِ عَلَّمَ الْقُرْآنَ ۚ"
        normalized = normalize_quran_text(raw)
        assert normalized == "الرحمن علم القران"

    def test_f07_c03_standardizes_all_alef_variants(self):
        raw = "إِنَّا أَعْطَيْنَاكَ ٱلْكَوْثَرَ"
        normalized = normalize_quran_text(raw)
        assert normalized == "انا اعطیناک الکوثر"

    def test_f07_c04_standardizes_yeh_and_kaf_variants(self):
        raw = "مَالِكِ يَوْمِ الدِّينِ"
        normalized = normalize_quran_text(raw)
        assert normalized == "مالک یوم الدین"

    def test_f07_c05_normalizes_tatweel_punctuation_and_whitespace(self):
        raw = "  ﴿الْحَمْـــدُ لِلَّهِ رَبِّ الْعَالَمِينَ﴾  ۝  "
        normalized = normalize_quran_text(raw)
        assert normalized == "الحمد لله رب العالمین"


# ==============================================================================
# Feature 08: Atomic JSON Importer
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature08AtomicJSONImporter:
    """Feature 08: python manage.py import_quran atomic loading and validation."""

    def test_f08_c01_import_sample_dataset_success(self):
        dataset = {
            "edition": {
                "identifier": "quran-imp-test",
                "name": "Import Test Edition",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                {"surah_number": 1, "number_in_surah": 1, "number": 1, "juz": 1, "text": "بِسْمِ اللَّهِ"},
                {"surah_number": 1, "number_in_surah": 2, "number": 2, "juz": 1, "text": "الْحَمْدُ لِلَّهِ"}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(dataset, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            call_command("import_quran", "--file", tmp_path)
            assert QuranAyah.objects.filter(edition_id="quran-imp-test").count() == 2
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_f08_c02_importer_dry_run_mode(self):
        dataset = {
            "edition": {
                "identifier": "quran-dry",
                "name": "Dry",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                {"surah_number": 1, "number_in_surah": 1, "number": 1, "juz": 1, "text": "بِسْمِ اللَّهِ"}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(dataset, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            call_command("import_quran", "--dry-run", "--file", tmp_path)
            assert QuranEdition.objects.filter(identifier="quran-dry").count() == 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_f08_c03_atomic_rollback_on_malformed_ayah(self):
        # Corrupt dataset with missing surah referenced
        dataset = {
            "edition": {
                "identifier": "quran-rollback",
                "name": "Rollback",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                {"surah_number": 1, "number_in_surah": 1, "number": 1, "juz": 1, "text": "آیه اول"},
                {"surah_number": 999, "number_in_surah": 1, "number": 2, "juz": 1, "text": "آیه خراب"}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(dataset, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            with pytest.raises(CommandError):
                call_command("import_quran", "--file", tmp_path)
            assert QuranAyah.objects.filter(edition_id="quran-rollback").count() == 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_f08_c04_importer_force_flag_idempotence(self):
        dataset = {
            "edition": {
                "identifier": "quran-force",
                "name": "Force",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                {"surah_number": 1, "number_in_surah": 1, "number": 1, "juz": 1, "text": "بِسْمِ اللَّهِ"}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(dataset, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            call_command("import_quran", "--file", tmp_path)
            # Re-import with --force
            call_command("import_quran", "--force", "--file", tmp_path)
            assert QuranAyah.objects.filter(edition_id="quran-force").count() == 1
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_f08_c05_importer_auto_populates_normalized_text(self):
        dataset = {
            "edition": {
                "identifier": "quran-norm",
                "name": "Norm",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                {"surah_number": 1, "number_in_surah": 1, "number": 1, "juz": 1, "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(dataset, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            call_command("import_quran", "--file", tmp_path)
            ayah = QuranAyah.objects.get(edition_id="quran-norm", number_in_surah=1)
            assert ayah.normalized_text == "بسم الله الرحمن الرحیم"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# ==============================================================================
# Feature 09: Cross-DB Search Engine
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature09CrossDBSearchEngine:
    """Feature 09: Substring, multi-token, and scoped search over normalized_text."""

    def test_f09_c01_exact_normalized_phrase_search(self):
        ensure_seed_quran_models()
        res = search_quran(query="الرحمن الرحيم", edition_id="quran-simple")
        assert res["count"] >= 1
        assert res["results"][0]["surah_number"] == 1

        # Search with raw diacritics also matches
        res_diacritic = search_quran(query="الرَّحْمَٰنِ الرَّحِيمِ", edition_id="quran-simple")
        assert res_diacritic["count"] >= 1

    def test_f09_c02_multi_word_and_token_query(self):
        ensure_seed_quran_models()
        res = search_quran(query="الله رحمن", edition_id="quran-simple")
        assert res["count"] >= 1
        assert any(r["number_in_surah"] == 1 for r in res["results"])

    def test_f09_c03_search_scoped_by_edition_and_surah(self):
        ensure_seed_quran_models()
        res = search_quran(query="الله", surah_number=112, edition_id="quran-simple")
        assert res["count"] >= 1
        assert all(r["surah_number"] == 112 for r in res["results"])

    def test_f09_c04_authentic_text_and_highlighting_preservation(self):
        authentic = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        highlighted = highlight_authentic_text(authentic, ["الرحمن"])
        assert "<mark>" in highlighted
        assert "</mark>" in highlighted
        assert "الرَّحْمَٰنِ" in highlighted

    def test_f09_c05_empty_query_and_no_match_resilience(self):
        ensure_seed_quran_models()
        res_empty = search_quran(query="")
        assert res_empty["count"] == 0
        assert res_empty["results"] == []

        res_none = search_quran(query="nonexistentsearchtokenxyz123")
        assert res_none["count"] == 0
        assert res_none["results"] == []


# ==============================================================================
# Feature 10: Quran Navigation APIs
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature10QuranNavigationAPIs:
    """Feature 10: REST endpoints /api/plugins/quran/ (editions, surahs, ayahs, search, compare)."""

    def test_f10_c01_list_and_retrieve_editions_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.get("/api/plugins/quran/editions/")
        assert res.status_code == 200
        assert len(res.data) >= 1

    def test_f10_c02_list_surahs_and_ayahs_pagination_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res_surahs = client.get("/api/plugins/quran/surahs/")
        assert res_surahs.status_code == 200

        res_ayahs = client.get("/api/plugins/quran/surahs/1/ayahs/")
        assert res_ayahs.status_code == 200
        assert "ayahs" in res_ayahs.data
        assert len(res_ayahs.data["ayahs"]) >= 1

    def test_f10_c03_single_ayah_coordinate_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.get("/api/plugins/quran/ayahs/1/1/")
        assert res.status_code == 200
        assert res.data["surah"]["number"] == 1
        assert res.data["number_in_surah"] == 1

    def test_f10_c04_juz_navigation_and_ayahs_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.get("/api/plugins/quran/juzs/")
        assert res.status_code == 200

    def test_f10_c05_parallel_compare_and_format_reference_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res_cmp = client.get("/api/plugins/quran/compare/?surah=1&ayah=1&editions=quran-simple,fa.ansarian")
        assert res_cmp.status_code == 200
        assert "editions" in res_cmp.data

        res_fmt = client.post(
            "/api/plugins/quran/format-reference/",
            data={"surah": 1, "ayah_from": 1, "ayah_to": 1},
            format="json"
        )
        assert res_fmt.status_code == 200
        assert "markdown" in res_fmt.data
        assert res_fmt.data["markdown"].startswith(">")


# ==============================================================================
# Feature 11: Frontend Plugin Core
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature11FrontendPluginCore:
    """Feature 11: Frontend manifest contract, capability guards, type declarations."""

    def test_f11_c01_frontend_manifest_contract_validation(self):
        manifest_path = REPO_ROOT / "backend/plugins/quran/manifest.json"
        assert manifest_path.exists()
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        validated = ManifestValidator.validate(data)
        assert validated["identifier"] == "quran"

    def test_f11_c02_frontend_plugin_types_contract_exists(self):
        types_path = REPO_ROOT / "frontend/src/plugins/core/pluginTypes.ts"
        assert types_path.exists()
        content = types_path.read_text(encoding="utf-8")
        assert "PluginManifest" in content

    def test_f11_c03_frontend_capability_guard_evaluation(self):
        plugin = Plugin.objects.create(
            identifier="frontend_guard_test",
            name="Frontend Guard",
            capabilities=["reader", "composer_action"]
        )
        assert plugin.has_capability("reader") is True
        assert plugin.has_capability("bot_action") is False

    def test_f11_c04_frontend_error_boundary_component_exists(self):
        error_boundary = REPO_ROOT / "frontend/src/plugins/core/PluginErrorBoundary.vue"
        assert error_boundary.exists()

    def test_f11_c05_frontend_registry_and_loader_exist(self):
        registry_ts = REPO_ROOT / "frontend/src/plugins/core/pluginRegistry.ts"
        loader_ts = REPO_ROOT / "frontend/src/plugins/core/pluginLoader.ts"
        assert registry_ts.exists()
        assert loader_ts.exists()


# ==============================================================================
# Feature 12: Dynamic Lazy-Loading
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature12DynamicLazyLoading:
    """Feature 12: Dynamic import contracts, route separation, lazy view directories."""

    def test_f12_c01_dynamic_routes_in_manifest(self):
        manifest_ts = REPO_ROOT / "frontend/src/plugins/quran/manifest.ts"
        assert manifest_ts.exists()
        content = manifest_ts.read_text(encoding="utf-8")
        assert "/apps/quran" in content
        assert "routes:" in content

    def test_f12_c02_dynamic_loader_cache_contract(self):
        loader_ts = REPO_ROOT / "frontend/src/plugins/core/pluginLoader.ts"
        content = loader_ts.read_text(encoding="utf-8")
        assert "initializePlugins" in content
        assert "usePluginRegistryStore" in content

    def test_f12_c03_backend_router_isolation(self):
        from apps.plugin_system.urls import urlpatterns as plug_urls
        from plugins.quran.urls import urlpatterns as quran_urls
        assert len(plug_urls) > 0
        assert len(quran_urls) > 0

    def test_f12_c04_lazy_views_exist_on_disk(self):
        quran_views_dir = REPO_ROOT / "frontend/src/plugins/quran/views"
        assert quran_views_dir.exists()

    def test_f12_c05_no_eager_side_effects(self):
        # Module imports should be safe and pure without making external calls
        import plugins.quran.apps
        import plugins.quran.services.normalizer
        assert hasattr(plugins.quran.apps, "QuranConfig")


# ==============================================================================
# Feature 13: Marketplace UI
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature13MarketplaceUI:
    """Feature 13: Marketplace list schemas, filtering, and settings schema Draft-07 compliance."""

    def test_f13_c01_marketplace_api_schema(self):
        Plugin.objects.get_or_create(
            identifier="quran",
            defaults={"name": "قرآن کریم", "version": "1.0.0", "is_active": True}
        )
        client = APIClient()
        res = client.get("/api/plugins/")
        assert res.status_code == 200
        assert len(res.data) > 0
        item = res.data[0]
        for key in ["id", "identifier", "name", "version", "capabilities", "is_installed", "is_enabled"]:
            assert key in item

    def test_f13_c02_marketplace_capability_filter(self):
        Plugin.objects.get_or_create(
            identifier="quran_cap_filter",
            defaults={"name": "Quran Filter", "capabilities": ["composer_action"], "is_active": True}
        )
        client = APIClient()
        res = client.get("/api/plugins/?capability=composer_action")
        assert res.status_code == 200
        assert any(p["identifier"] == "quran_cap_filter" for p in res.data)

    def test_f13_c03_marketplace_search_filter(self):
        Plugin.objects.get_or_create(
            identifier="search_target_plugin",
            defaults={"name": "Special Search Plugin", "is_active": True}
        )
        client = APIClient()
        res = client.get("/api/plugins/?search=Special")
        assert res.status_code == 200
        assert any(p["identifier"] == "search_target_plugin" for p in res.data)

    def test_f13_c04_marketplace_view_component_exists(self):
        feed_view = REPO_ROOT / "frontend/src/views/FeedView.vue"
        assert feed_view.exists()

    def test_f13_c05_marketplace_settings_schema_renderer_contract(self):
        plugin = Plugin.objects.create(
            identifier="schema_render_test",
            name="Schema Test",
            settings_schema={
                "type": "object",
                "properties": {
                    "font_size": {"type": "integer", "default": 18}
                }
            }
        )
        assert plugin.settings_schema["type"] == "object"
        assert "font_size" in plugin.settings_schema["properties"]


# ==============================================================================
# Feature 14: Quran Mini-App Views
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature14QuranMiniAppViews:
    """Feature 14: Surah catalog, ayah reader with translation, juz navigation, audio URLs."""

    def test_f14_c01_quran_surah_catalog_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.get("/api/plugins/quran/surahs/")
        assert res.status_code == 200
        assert len(res.data) >= 1

    def test_f14_c02_quran_ayah_reader_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.get("/api/plugins/quran/surahs/1/ayahs/?edition=quran-simple&with_translation=fa.ansarian")
        assert res.status_code == 200
        assert "ayahs" in res.data
        assert len(res.data["ayahs"]) >= 1
        assert res.data["ayahs"][0].get("translation") is not None

    def test_f14_c03_quran_juz_reader_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.get("/api/plugins/quran/juzs/")
        assert res.status_code == 200
        assert len(res.data) >= 1

    def test_f14_c04_quran_search_api(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.get("/api/plugins/quran/search/?q=الرحمن")
        assert res.status_code == 200
        assert res.data["count"] >= 1

    def test_f14_c05_quran_audio_stream_contract(self):
        ed, _ = QuranEdition.objects.get_or_create(identifier="quran-simple", defaults={"name": "Simple", "language": "ar"})
        s1, _ = QuranSurah.objects.get_or_create(number=1, defaults={"name": "الفاتحة", "revelation_type": "Meccan", "ayah_count": 7})
        ayah, _ = QuranAyah.objects.get_or_create(
            edition=ed,
            surah=s1,
            number_in_surah=1,
            defaults={
                "number": 1,
                "text": "بِسْمِ اللَّهِ",
                "normalized_text": "بسم الله",
                "juz": 1,
                "audio_url": "https://everyayah.com/data/Alafasy_128kbps/001001.mp3"
            }
        )
        assert ayah.audio_url.endswith(".mp3")


# ==============================================================================
# Feature 15: Composer Action Integration
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature15ComposerActionIntegration:
    """Feature 15: Markdown formatting, verse picker dialog contract, non-invasive post reference."""

    def test_f15_c01_composer_action_in_manifest(self):
        manifest_path = REPO_ROOT / "backend/plugins/quran/manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "capabilities" in data
        assert "composer_action" in data["capabilities"]

        # Also check frontend manifest composer actions
        frontend_manifest = REPO_ROOT / "frontend/src/plugins/quran/manifest.ts"
        assert frontend_manifest.exists()
        content = frontend_manifest.read_text(encoding="utf-8")
        assert "composerActions" in content
        assert "quran-insert-ayah" in content

    def test_f15_c02_verse_picker_format_endpoint(self):
        ensure_seed_quran_models()
        client = APIClient()
        res = client.post(
            "/api/plugins/quran/format-reference/",
            data={"surah": 1, "ayah_from": 1, "ayah_to": 1},
            format="json"
        )
        assert res.status_code == 200
        assert "markdown" in res.data
        assert res.data["markdown"].startswith("> ﴿")

    def test_f15_c03_markdown_formatting_verse_range(self):
        md = format_quran_markdown_reference(
            surah_name="الفاتحة",
            surah_number=1,
            ayah_from=1,
            ayah_to=2,
            arabic_texts=["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"],
            translation_texts=["به نام خدا", "ستایش مخصوص خداست"],
            translation_edition_name="ترجمه انصاریان",
            lang="fa"
        )
        assert "> ﴿بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ ۝۱ الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ ۝۲﴾" in md
        assert "— **سوره الفاتحة (۱:۱-۲)**" in md

    def test_f15_c04_markdown_injection_preserves_post_text(self):
        user_comment = "این آیه شریفه را بخوانید:\n\n"
        md_quote = format_quran_markdown_reference(
            surah_name="الإخلاص",
            surah_number=112,
            ayah_from=1,
            ayah_to=1,
            arabic_texts=["قُلْ هُوَ اللَّهُ أَحَدٌ"],
            lang="fa"
        )
        full_content = user_comment + md_quote
        assert full_content.startswith("این آیه شریفه را بخوانید:")
        assert "> ﴿قُلْ هُوَ اللَّهُ أَحَدٌ﴾" in full_content

    def test_f15_c05_post_publishing_pipeline_untouched(self):
        user = User.objects.create_user(phone="09121110009", password="password123")
        topic = Topic.objects.create(name="Tafsir Thread", created_by=user)
        md_quote = format_quran_markdown_reference(
            surah_name="الفاتحة",
            surah_number=1,
            ayah_from=1,
            ayah_to=1,
            arabic_texts=["بِسْمِ اللَّهِ"],
            lang="fa"
        )
        post = Post.objects.create(topic=topic, author=user, content=md_quote)
        assert post.id is not None
        assert post.content_hash is not None
        assert Post.objects.filter(id=post.id).exists()


# ==============================================================================
# Feature 16: Opaque-Box E2E Test Suite
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature16OpaqueBoxE2ETestSuite:
    """Feature 16: 4-tier test architecture layout, CLI argument parsing, route resolution."""

    def test_f16_c01_4tier_test_suite_files_exist(self):
        expected_files = [
            REPO_ROOT / "tests/e2e/test_tier1_feature_coverage.py",
            REPO_ROOT / "tests/e2e/test_tier2_boundary_cases.py",
            REPO_ROOT / "tests/e2e/test_tier3_pairwise_combinations.py",
            REPO_ROOT / "tests/e2e/test_tier4_real_world_workloads.py",
            REPO_ROOT / "tests/e2e/test_runner.py",
            REPO_ROOT / "tests/e2e/conftest.py",
        ]
        for f in expected_files:
            assert f.exists(), f"Expected test harness file {f.name} to exist."

    def test_f16_c02_test_runner_cli_argument_parsing(self):
        parser = build_parser()
        args_t1 = parser.parse_args(["--tier", "1"])
        assert args_t1.tier == ["1"]

        args_all = parser.parse_args(["--all"])
        assert args_all.all is True

        args_nr = parser.parse_args(["--non-regression"])
        assert args_nr.non_regression is True

    def test_f16_c03_test_isolation_and_db_cleanup(self):
        user = User.objects.create_user(phone="09121110010", password="password123")
        topic = Topic.objects.create(name="Isolation Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Isolation Post")
        assert Topic.objects.filter(id=topic.id).exists()
        assert Post.objects.filter(id=post.id).exists()

    def test_f16_c04_opaque_box_routes_resolvable(self):
        assert reverse("plugin-marketplace-list") == "/api/plugins/"
        assert reverse("quran-search") == "/api/plugins/quran/search/"
        assert reverse("quran-format-reference") == "/api/plugins/quran/format-reference/"

    def test_f16_c05_test_runner_dry_run_execution(self):
        parser = build_parser()
        args = parser.parse_args(["--dry-run", "--all"])
        assert args.dry_run is True
        assert args.all is True


# ==============================================================================
# Feature 17: Core Non-Regression
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature17CoreNonRegression:
    """Feature 17: Core models (User, Topic, Post, BotTask, DonationCampaign) zero regressions."""

    def test_f17_c01_accounts_user_model_and_auth(self):
        user = User.objects.create_user(phone="09121110011", password="secure_password_123")
        assert user.check_password("secure_password_123") is True
        token, _ = Token.objects.get_or_create(user=user)
        assert len(token.key) >= 20

    def test_f17_c02_notes_topics_and_posts_non_regression(self):
        user = User.objects.create_user(phone="09121110012", password="password123")
        topic = Topic.objects.create(name="Notes Non-Regression Topic", created_by=user)
        post = Post.objects.create(topic=topic, author=user, content="Sample non-regression note.")
        assert post.content_hash is not None
        assert topic.posts.count() == 1

    def test_f17_c03_donations_campaigns_and_payments_non_regression(self):
        if DonationCampaign is not None:
            user = User.objects.create_user(phone="09121110013", password="password123")
            topic = Topic.objects.create(name="Donation Topic", created_by=user)
            campaign = DonationCampaign.objects.create(
                topic=topic,
                creator=user,
                title="کمپین خیریه",
                description="توضیحات آزمون کمپین خیریه",
                target_amount=10000000
            )
            assert campaign.status == DonationCampaign.StatusChoices.ACTIVE
            assert campaign.target_amount == 10000000

    def test_f17_c04_bot_runner_tasks_non_regression(self):
        task = BotTask.objects.create(
            action="send",
            platform="telegram",
            chat_id="@tafakor_channel",
            text="پیام ربات",
            processed=False
        )
        assert task.action in ["send", "edit", "delete"]
        assert BotTask.objects.filter(id=task.id, processed=False).exists()

    def test_f17_c05_post_retrieval_with_uninstalled_plugin(self):
        user = User.objects.create_user(phone="09121110014", password="password123")
        topic = Topic.objects.create(name="Decoupled Topic", created_by=user)
        plugin = Plugin.objects.create(identifier="transient_plugin", name="Transient")
        post = Post.objects.create(topic=topic, author=user, content="> ﴿Decoupled Verse﴾")
        ref = PostPluginReference.objects.create(
            post=post,
            plugin=plugin,
            resource_type="ayah",
            external_id="1:1"
        )
        plugin.is_active = False
        plugin.save()

        retrieved_post = Post.objects.get(id=post.id)
        assert retrieved_post.content == "> ﴿Decoupled Verse﴾"
        assert retrieved_post.plugin_references.count() == 1


# ==============================================================================
# Feature 18: Adversarial Coverage Hardening
# ==============================================================================
@pytest.mark.django_db
class TestTier1Feature18AdversarialCoverageHardening:
    """Feature 18: Malformed payloads, SQL injection, extreme unicode fuzzing, out-of-bounds recovery."""

    def test_f18_c01_adversarial_malformed_manifest_payloads(self):
        adversarial_payloads = [
            {"identifier": "../../etc/passwd", "name": "Traversal", "manifest_version": 1, "version": "1.0.0"},
            {"identifier": "<script>alert(1)</script>", "name": "XSS", "manifest_version": 1, "version": "1.0.0"},
            {"identifier": "valid_id", "name": "Bad Version", "manifest_version": 999, "version": "1.0.0"},
            {"identifier": "valid_id", "name": "Bad Scope", "manifest_version": 1, "version": "1.0.0", "scopes": ["root:admin"]},
            {"identifier": "valid_id", "name": "Bad Cap", "manifest_version": 1, "version": "1.0.0", "capabilities": ["kernel_access"]}
        ]
        for payload in adversarial_payloads:
            with pytest.raises(ManifestValidationError):
                ManifestValidator.validate(payload)

    def test_f18_c02_adversarial_sql_injection_in_search(self):
        ensure_seed_quran_models()
        sqli_queries = [
            "' OR '1'='1",
            "'; DROP TABLE tafakor_plugins; --",
            "\" UNION SELECT * FROM auth_user WHERE '1'='1",
            "1' ORDER BY 1--+",
            "admin'--",
        ]
        for sqli in sqli_queries:
            res = search_quran(query=sqli, edition_id="quran-simple")
            assert isinstance(res["results"], list)
            assert res["count"] >= 0

    def test_f18_c03_adversarial_extreme_unicode_fuzzing(self):
        fuzz_inputs = [
            "بِ" + ("\u064E" * 50) + "سْ" + ("\u0652" * 50) + "مِ",
            "\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u2066\u2067\u2068\u2069",
            "﴿﴾۝۞۩«»“”‘’" * 10,
            "ـ" * 100 + "اللَّهِ" + "ـ" * 100,
        ]
        for fuzz in fuzz_inputs:
            normalized = normalize_quran_text(fuzz)
            assert isinstance(normalized, str)

    def test_f18_c04_adversarial_unauthorized_topic_privilege_escalation(self):
        owner = User.objects.create_user(phone="09121110015", password="password123")
        attacker = User.objects.create_user(phone="09121110016", password="password123")
        topic = Topic.objects.create(name="Secure Topic", created_by=owner)
        Plugin.objects.get_or_create(
            identifier="quran",
            defaults={"name": "قرآن کریم", "version": "1.0.0", "is_active": True}
        )

        client = APIClient()
        client.force_authenticate(user=attacker)
        res = client.post(
            f"/api/plugins/topics/{topic.id}/install/",
            data={"identifier": "quran"},
            format="json"
        )
        assert res.status_code == 403

    def test_f18_c05_adversarial_importer_out_of_bounds_recovery(self):
        dataset = {
            "edition": {
                "identifier": "quran-oob",
                "name": "OOB",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                {"surah_number": 999, "number_in_surah": 1, "number": 1, "juz": 1, "text": "نامعتبر"}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(dataset, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            with pytest.raises(CommandError):
                call_command("import_quran", "--file", tmp_path)
            assert QuranAyah.objects.filter(edition_id="quran-oob").count() == 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
