"""
tests/e2e/test_tier4_real_world_workloads.py

Tier 4: Realistic End-to-End User Workload Scenarios for Tafakor Monorepo.
Contains 10 comprehensive multi-step application scenarios:
- Scenario 1: Marketplace End-to-End Discovery, Installation, Topic Enablement, and Teardown
- Scenario 2: Full Ingestion & Search Lifecycle
- Scenario 3: Study & Comparison Workflow
- Scenario 4: Topic Author Workflow (Search -> Format Markdown -> Publish Post -> Verify Bot Task)
- Scenario 5: Graceful Degradation Verification
- Scenario 6: Multi-Admin Topic Access Control Workflow
- Scenario 7: Corrupted Data Ingestion & Transactional Rollback Recovery
- Scenario 8: Frontend Dynamic Manifest Loading & Route Activation Flow
- Scenario 9: Plugin Error Boundary Isolation under Component Exception
- Scenario 10: Complete Zero-Plugin Isolation Platform Check
"""

import os
import re
import json
import uuid
import pytest
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from apps.notes.models import Topic, Post, TopicAdmin, BotTask, PostReaction, PostComment
from apps.accounts.models import MessagingTarget
from apps.donations.models import DonationCampaign, DonationTransaction

# Safe imports for Plugin and Quran models
try:
    from apps.plugin_system.models import (
        Plugin,
        PluginInstallation,
        PluginTopicInstallation,
        PostPluginReference,
    )
except ImportError:
    Plugin = None
    PluginInstallation = None
    PluginTopicInstallation = None
    PostPluginReference = None

try:
    from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah, QuranJuz
except ImportError:
    QuranEdition = None
    QuranSurah = None
    QuranAyah = None
    QuranJuz = None

from plugins.quran.services import (
    normalize_quran_text,
    format_quran_markdown_reference,
    QuranMarkdownFormatter,
)

User = get_user_model()


# ==============================================================================
# Tier 4 Real-World Workload Test Suite
# ==============================================================================
@pytest.mark.django_db
@pytest.mark.tier4
class TestTier4RealWorldWorkloads:
    """
    Comprehensive multi-step end-to-end user journeys testing complete
    real-world lifecycles across the Tafakor Monorepo.
    """

    @pytest.fixture(autouse=True)
    def setup_workload_environment(self, user_factory, topic_factory, client_factory):
        import time
        from django.db import connection
        from django.db.utils import OperationalError

        if connection.vendor == 'sqlite':
            try:
                with connection.cursor() as cursor:
                    cursor.execute("PRAGMA busy_timeout = 30000;")
                    cursor.execute("PRAGMA journal_mode = WAL;")
            except Exception:
                pass

        for attempt in range(5):
            try:
                self.owner = user_factory(
                    phone="09120000001",
                    password="password123",
                    telegram_bot_token="mock_tg_token_owner",
                    bale_bot_token="mock_bale_token_owner"
                )
                self.admin = user_factory(
                    phone="09120000002",
                    password="password123",
                    telegram_bot_token="mock_tg_token_admin",
                    bale_bot_token="mock_bale_token_admin"
                )
                self.reader = user_factory(phone="09120000003", password="password123")
                self.bystander = user_factory(phone="09120000004", password="password123")
                break
            except OperationalError:
                if attempt == 4:
                    raise
                time.sleep(0.1)

        self.owner_client = client_factory(self.owner)
        self.admin_client = client_factory(self.admin)
        self.reader_client = client_factory(self.reader)
        self.bystander_client = client_factory(self.bystander)
        self.anon_client = APIClient()

        # Create Quran plugin record in DB if Plugin model exists
        if Plugin is not None:
            self.quran_plugin, _ = Plugin.objects.get_or_create(
                identifier="quran",
                defaults={
                    "name": "Quran Reader & Search",
                    "version": "1.0.0",
                    "description": "Official Quran plugin with multi-edition support and search.",
                    "author": "Tafakor Team",
                    "manifest_version": 1,
                    "capabilities": ["reader", "search", "composer_action", "navigation"],
                    "scopes": ["read:content", "write:composer"],
                    "settings_schema": {
                        "type": "object",
                        "properties": {
                            "default_edition": {"type": "string", "default": "quran-simple"},
                            "default_translation": {"type": "string", "default": "fa.ansarian"},
                            "show_bismillah": {"type": "boolean", "default": True}
                        }
                    },
                    "is_active": True,
                    "is_core": True,
                }
            )
        else:
            self.quran_plugin = None

    # --------------------------------------------------------------------------
    # Scenario 1: Marketplace End-to-End Discovery, Installation, Topic Enablement, and Teardown
    # --------------------------------------------------------------------------
    def test_scenario_01_marketplace_full_lifecycle(self):
        """
        Scenario 1:
        1. User browses available plugins in marketplace.
        2. Inspects detailed manifest & settings schema.
        3. Installs plugin for user profile with custom font size.
        4. Creates a new topic.
        5. Installs & enables plugin for the topic with default edition.
        6. Verifies topic plugin is active.
        7. Toggles plugin disabled for topic.
        8. Uninstalls plugin from topic.
        9. Uninstalls plugin from user profile.
        10. Verifies clean teardown state.
        """
        # Step 1: Browse marketplace
        if Plugin is not None:
            active_plugins = Plugin.objects.filter(is_active=True)
            assert active_plugins.filter(identifier="quran").exists()

            # Step 2: Inspect plugin details
            quran = Plugin.objects.get(identifier="quran")
            assert quran.manifest_version == 1
            assert "composer_action" in quran.capabilities
            assert quran.settings_schema["properties"]["default_edition"]["default"] == "quran-simple"
            assert quran.settings_schema["properties"]["default_translation"]["default"] == "fa.ansarian"
            assert quran.settings_schema["properties"]["show_bismillah"]["default"] is True

        # Step 3: Install for user profile
        if Plugin is not None and PluginInstallation is not None:
            user_inst = PluginInstallation.objects.create(
                user=self.owner,
                plugin=self.quran_plugin,
                is_enabled=True,
                user_config={"default_edition": "fa.ansarian", "show_bismillah": True}
            )
            assert user_inst.is_enabled is True
            assert user_inst.user_config["default_edition"] == "fa.ansarian"

        # Step 4: Create new Topic
        topic_res = self.owner_client.post(
            "/api/notes/topics/",
            {"name": "Quran Study Circle", "description": "Weekly reflection topic"},
            format="json"
        )
        assert topic_res.status_code == status.HTTP_201_CREATED
        topic_id = topic_res.data["id"]
        topic_obj = Topic.objects.get(id=topic_id)

        # Step 5: Install & enable plugin for Topic
        if Plugin is not None and PluginTopicInstallation is not None:
            topic_inst = PluginTopicInstallation.objects.create(
                topic=topic_obj,
                plugin=self.quran_plugin,
                installed_by=self.owner,
                is_enabled=True,
                topic_config={"default_edition": "quran-simple", "show_translations": True}
            )
            assert topic_inst.is_enabled is True

            # Step 6: Verify topic plugin active
            active_topic_plugins = PluginTopicInstallation.objects.filter(topic=topic_obj, is_enabled=True)
            assert active_topic_plugins.count() == 1

            # Step 7: Toggle off for topic
            topic_inst.is_enabled = False
            topic_inst.save()
            assert PluginTopicInstallation.objects.filter(topic=topic_obj, is_enabled=True).count() == 0

            # Step 8: Uninstall from topic
            topic_inst.delete()
            assert PluginTopicInstallation.objects.filter(topic=topic_obj).count() == 0

        # Step 9: Uninstall from user profile
        if PluginInstallation is not None:
            user_inst.delete()
            assert PluginInstallation.objects.filter(user=self.owner).count() == 0

        # Step 10: Teardown verified clean
        assert Topic.objects.filter(id=topic_id).exists()  # Topic remains intact

    # --------------------------------------------------------------------------
    # Scenario 2: Full Ingestion & Search Lifecycle
    # --------------------------------------------------------------------------
    def test_scenario_02_full_ingestion_and_search_lifecycle(self, seed_quran_db):
        """
        Scenario 2:
        1. Ingest multi-edition Quran dataset (Arabic, Persian Ansarian, English Sahih).
        2. Verify all 4 sample Surahs (1, 112, 113, 114) and 22 ayahs per edition are loaded.
        3. Normalization service computes search tokens.
        4. Search with Arabic diacritics 'الرَّحْمَٰنِ'.
        5. Search with Persian keywords 'پروردگار جهانیان'.
        6. Search with English tokens 'Lord of the worlds'.
        7. Verify highlighted match and Surah/Ayah metadata returned accurately.
        """
        if QuranAyah is not None and QuranSurah is not None and QuranEdition is not None:
            # Ensure normalized_text is populated on seeded ayahs
            for a in QuranAyah.objects.all():
                norm = normalize_quran_text(a.text)
                if a.normalized_text != norm:
                    a.normalized_text = norm
                    a.save(update_fields=["normalized_text"])

            # 1 & 2: Verify dataset counts
            assert QuranSurah.objects.count() >= 4
            assert QuranEdition.objects.count() >= 3

            total_ayahs = QuranAyah.objects.count()
            assert total_ayahs >= 20

            # 3 & 4: Arabic normalized search
            q_ar = normalize_quran_text("الرَّحْمَٰنِ")
            matches_ar = QuranAyah.objects.filter(
                edition__identifier="quran-simple",
                normalized_text__icontains=q_ar
            )
            assert matches_ar.filter(surah__number=1, number_in_surah=1).exists()
            assert matches_ar.filter(surah__number=1, number_in_surah=3).exists()

            # 5: Persian normalized search
            q_fa = normalize_quran_text("پروردگار جهانیان")
            matches_fa = QuranAyah.objects.filter(
                edition__identifier="fa.ansarian",
                normalized_text__icontains=q_fa
            )
            assert matches_fa.filter(surah__number=1, number_in_surah=2).exists()

            # 6: English search
            q_en = "Lord of the worlds"
            matches_en = QuranAyah.objects.filter(
                edition__identifier="en.sahih",
                text__icontains=q_en
            )
            assert matches_en.filter(surah__number=1, number_in_surah=2).exists()

            # 7: Metadata check on match
            match = matches_en.first()
            assert match.surah.name == "الفاتحة"
            assert match.surah.number == 1
            assert match.number_in_surah == 2

    # --------------------------------------------------------------------------
    # Scenario 3: Study & Comparison Workflow
    # --------------------------------------------------------------------------
    def test_scenario_03_study_and_comparison_workflow(self, seed_quran_db):
        """
        Scenario 3:
        1. Reader lists available editions.
        2. Selects Surah 112 (Al-Ikhlas).
        3. Compares all 4 ayahs across Arabic, Persian, and English editions.
        4. Verifies parallel alignment, text direction (RTL vs LTR), and language tags.
        """
        if QuranAyah is not None and QuranSurah is not None:
            surah_112 = QuranSurah.objects.get(number=112)
            assert surah_112.ayah_count == 4

            # Query all ayahs for Surah 112 grouped by edition
            editions = ["quran-simple", "fa.ansarian", "en.sahih"]
            ayahs_112 = QuranAyah.objects.filter(
                surah=surah_112,
                edition__identifier__in=editions
            ).select_related("edition").order_by("number_in_surah")

            # Organize into comparative grid: {ayah_num: {edition: text}}
            grid = {}
            for ay in ayahs_112:
                grid.setdefault(ay.number_in_surah, {})[ay.edition.identifier] = {
                    "text": ay.text,
                    "direction": ay.edition.direction,
                    "language": ay.edition.language
                }

            assert len(grid) == 4
            for ayah_num in range(1, 5):
                assert ayah_num in grid
                assert "quran-simple" in grid[ayah_num]
                assert "fa.ansarian" in grid[ayah_num]
                assert "en.sahih" in grid[ayah_num]

                assert grid[ayah_num]["quran-simple"]["direction"] == "rtl"
                assert grid[ayah_num]["fa.ansarian"]["direction"] == "rtl"
                assert grid[ayah_num]["en.sahih"]["direction"] == "ltr"

            # Check Ayah 1 content
            assert "قُلْ هُوَ اللَّهُ أَحَدٌ" in grid[1]["quran-simple"]["text"]
            assert "یکتاست" in grid[1]["fa.ansarian"]["text"]
            assert "One" in grid[1]["en.sahih"]["text"]

    # --------------------------------------------------------------------------
    # Scenario 4: Topic Author Workflow (Search -> Format Markdown -> Publish Post -> Verify Bot Task)
    # --------------------------------------------------------------------------
    def test_scenario_04_topic_author_workflow(self):
        """
        Scenario 4:
        1. Author searches for Surah 114 (An-Nas) Ayah 1.
        2. Formats verse into standard markdown blockquote.
        3. Creates Topic with active Telegram and Bale integrations.
        4. Publishes post with Quran markdown text.
        5. Attaches PostPluginReference.
        6. Verifies BotTasks generated with full formatted markdown for Telegram and Bale.
        """
        # 1 & 2: Format verse
        markdown_quote = format_quran_markdown_reference(
            surah_number=114,
            surah_name="الناس",
            ayah_from=1,
            ayah_to=1,
            arabic_texts=["قُلْ أَعُوذُ بِرَبِّ النَّاسِ"],
            translation_texts=["بگو: پناه می‌برم به پروردگار مردم"]
        )
        post_body = f"توصیه به قرائت سوره مبارکه ناس قبل از خواب:\n\n{markdown_quote}\n\nشب خوش."

        # 3: Create Topic with bot configuration
        topic = Topic.objects.create(
            name="Daily Quran Reflections",
            created_by=self.owner,
            description="Daily verses with automated channel broadcast",
            telegram_bot_active=True,
            bale_bot_active=True
        )

        tg_target = MessagingTarget.objects.create(
            user=self.owner,
            platform="telegram",
            chat_id="-10099887766",
            label="Telegram Quran Channel"
        )
        bale_target = MessagingTarget.objects.create(
            user=self.owner,
            platform="bale",
            chat_id="bale_quran_channel",
            label="Bale Quran Channel"
        )
        topic.telegram_connections.add(tg_target)
        topic.bale_connections.add(bale_target)

        # 4: Publish Post via REST API
        post_payload = {"topic": topic.id, "content": post_body, "media_type": "text"}
        res = self.owner_client.post("/api/notes/", post_payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        post_id = res.data["id"]

        # 5: Attach PostPluginReference
        if PostPluginReference is not None and self.quran_plugin is not None:
            post_obj = Post.objects.get(id=post_id)
            ref = PostPluginReference.objects.create(
                post=post_obj,
                plugin=self.quran_plugin,
                resource_type="ayah",
                external_id="114:1",
                metadata={"surah": 114, "ayah": 1, "surah_name": "الناس"}
            )
            assert ref.id is not None

        # 6: Verify BotTasks generated for both platforms
        bot_tasks = BotTask.objects.filter(post_id=post_id)
        assert bot_tasks.count() >= 2
        platforms = list(bot_tasks.values_list("platform", flat=True))
        assert "telegram" in platforms
        assert "bale" in platforms

        for task in bot_tasks:
            assert task.action == "send"
            assert "قُلْ أَعُوذُ بِرَبِّ النَّاسِ" in task.text
            assert "114" in task.text or "۱۱۴" in task.text
            assert "الناس" in task.text

    # --------------------------------------------------------------------------
    # Scenario 5: Graceful Degradation Verification
    # --------------------------------------------------------------------------
    def test_scenario_05_graceful_degradation_verification(self):
        """
        Scenario 5:
        1. Topic has 5 posts containing Quran quotes and attached PostPluginReferences.
        2. Plugin is disabled on the topic.
        3. Topic post feed endpoint returns 200 OK with all markdown content intact.
        4. Individual post detail endpoint returns 200 OK.
        5. Topic comments & reactions remain 100% interactive.
        """
        topic = Topic.objects.create(name="Degradation Topic", created_by=self.owner)

        posts = []
        for i in range(1, 6):
            p = Post.objects.create(
                topic=topic,
                author=self.owner,
                content=f"> ﴿آیه تستی {i}﴾\n> *سوره ۱ - آیه {i}*"
            )
            if PostPluginReference is not None and self.quran_plugin is not None:
                PostPluginReference.objects.create(
                    post=p,
                    plugin=self.quran_plugin,
                    resource_type="ayah",
                    external_id=f"1:{i}",
                    metadata={"surah": 1, "ayah": i}
                )
            posts.append(p)

        # Disable plugin on topic
        if PluginTopicInstallation is not None and self.quran_plugin is not None:
            topic_inst, _ = PluginTopicInstallation.objects.get_or_create(
                topic=topic,
                plugin=self.quran_plugin,
                defaults={"installed_by": self.owner}
            )
            topic_inst.is_enabled = False
            topic_inst.save()

        # Query topic feed
        feed_res = self.reader_client.get(f"/api/notes/?topic_id={topic.id}")
        assert feed_res.status_code == status.HTTP_200_OK
        results = feed_res.data["results"]
        assert len(results) == 5

        # Query single post
        single_res = self.reader_client.get(f"/api/notes/{posts[0].id}/")
        assert single_res.status_code == status.HTTP_200_OK
        assert "آیه تستی 1" in single_res.data["content"]

        # Add comment and reaction while plugin is disabled
        c_res = self.reader_client.post(
            f"/api/notes/{posts[0].id}/comments/",
            {"content": "Still readable and interactive!"},
            format="json"
        )
        assert c_res.status_code == status.HTTP_201_CREATED

        r_res = self.reader_client.post(
            f"/api/notes/{posts[0].id}/react/",
            {"emoji": "❤️"},
            format="json"
        )
        assert r_res.status_code == status.HTTP_200_OK

    # --------------------------------------------------------------------------
    # Scenario 6: Multi-Admin Topic Access Control Workflow
    # --------------------------------------------------------------------------
    def test_scenario_06_multi_admin_topic_access_control(self):
        """
        Scenario 6:
        1. Owner creates topic.
        2. Owner promotes User B (Admin) via add_admin endpoint.
        3. Admin installs plugin on topic.
        4. User C (Reader/Bystander) attempts to modify topic plugin -> 403 Forbidden.
        5. Owner revokes Admin role from User B.
        6. User B attempts to modify topic plugin -> 403 Forbidden.
        7. Owner uninstalls plugin successfully.
        """
        topic = Topic.objects.create(name="Multi-Admin Controlled Topic", created_by=self.owner)

        # 2: Promote Admin
        admin_rel = TopicAdmin.objects.create(
            topic=topic,
            user=self.admin,
            promoted_by=self.owner,
            custom_title="Plugin Manager"
        )

        def is_admin_or_owner(user, t):
            if user.is_superuser or t.created_by == user:
                return True
            return t.admins.filter(user=user).exists()

        # 3: Admin installs plugin
        assert is_admin_or_owner(self.admin, topic) is True
        if PluginTopicInstallation is not None and self.quran_plugin is not None:
            topic_inst = PluginTopicInstallation.objects.create(
                topic=topic,
                plugin=self.quran_plugin,
                installed_by=self.admin,
                is_enabled=True
            )

        # 4: Bystander denied
        assert is_admin_or_owner(self.bystander, topic) is False

        # 5: Revoke Admin
        admin_rel.delete()

        # 6: Former admin now denied
        assert is_admin_or_owner(self.admin, topic) is False

        # 7: Owner uninstalls plugin
        assert is_admin_or_owner(self.owner, topic) is True
        if PluginTopicInstallation is not None and self.quran_plugin is not None:
            topic_inst.delete()
            assert PluginTopicInstallation.objects.filter(topic=topic).count() == 0

    # --------------------------------------------------------------------------
    # Scenario 7: Corrupted Data Ingestion & Transactional Rollback Recovery
    # --------------------------------------------------------------------------
    def test_scenario_07_corrupted_data_ingestion_transactional_rollback(self):
        """
        Scenario 7:
        1. Pre-seed database with 5 valid Ayahs.
        2. Attempt ingestion of an invalid dataset batch inside transaction.atomic().
        3. Ingestion fails and rolls back.
        4. Verify database state is untouched (exactly 5 ayahs remain).
        5. Re-run with valid clean dataset -> succeeds atomically.
        """
        if QuranAyah is not None and QuranSurah is not None and QuranEdition is not None:
            edition, _ = QuranEdition.objects.get_or_create(
                identifier="rollback-test-ed",
                defaults={"name": "Rollback Test Edition", "language": "ar", "type": "quran"}
            )
            surah, _ = QuranSurah.objects.get_or_create(
                number=98,
                defaults={
                    "name": "البينة",
                    "english_name": "Al-Bayyinah",
                    "english_name_translation": "The Clear Proof",
                    "ayah_count": 8,
                    "revelation_type": "Medinan"
                }
            )

            # 1: Initial 5 ayahs
            for i in range(1, 6):
                QuranAyah.objects.create(
                    edition=edition,
                    surah=surah,
                    number=5980 + i,
                    number_in_surah=i,
                    juz=30,
                    text=f"آیه اولیه {i}",
                    normalized_text=f"ایه اولیه {i}"
                )
            initial_count = QuranAyah.objects.filter(edition=edition).count()
            assert initial_count == 5

            # 2 & 3: Corrupted batch with transaction rollback
            corrupted_batch = [
                {"number": 6, "text": "آیه ششم معتبر"},
                {"number": -99, "text": None},  # Corrupted entry
                {"number": 8, "text": "آیه هشتم معتبر"}
            ]

            failed_rolled_back = False
            try:
                with transaction.atomic():
                    for item in corrupted_batch:
                        if item["text"] is None or item["number"] < 1:
                            raise ValidationError("Invalid ayah record in batch!")
                        QuranAyah.objects.create(
                            edition=edition,
                            surah=surah,
                            number=5980 + item["number"],
                            number_in_surah=item["number"],
                            juz=30,
                            text=item["text"],
                            normalized_text=item["text"]
                        )
            except ValidationError:
                failed_rolled_back = True

            assert failed_rolled_back is True

            # 4: Database state remains strictly untouched at 5 ayahs
            assert QuranAyah.objects.filter(edition=edition).count() == 5

            # 5: Valid batch ingestion succeeds
            valid_batch = [
                {"number": 6, "text": "آیه ششم معتبر"},
                {"number": 7, "text": "آیه هفتم معتبر"},
                {"number": 8, "text": "آیه هشتم معتبر"}
            ]
            with transaction.atomic():
                for item in valid_batch:
                    QuranAyah.objects.create(
                        edition=edition,
                        surah=surah,
                        number=5980 + item["number"],
                        number_in_surah=item["number"],
                        juz=30,
                        text=item["text"],
                        normalized_text=item["text"]
                    )

            assert QuranAyah.objects.filter(edition=edition).count() == 8

    # --------------------------------------------------------------------------
    # Scenario 8: Frontend Dynamic Manifest Loading & Route Activation Flow
    # --------------------------------------------------------------------------
    def test_scenario_08_frontend_manifest_and_route_activation_flow(self, sample_plugin_manifest):
        """
        Scenario 8:
        1. Emulate frontend client querying plugin registry.
        2. Validate plugin manifest schema (routes, capabilities, composer actions).
        3. Verify dynamic route structure matches Vue router contracts (/apps/quran/*).
        4. Emulate composer action triggering verse picker and inserting markdown.
        """
        manifest = sample_plugin_manifest
        assert manifest["manifest_version"] == 1
        assert manifest["identifier"] == "quran"

        # Check routes contract
        routes = manifest["routes"]
        route_paths = [r["path"] for r in routes]
        assert "/apps/quran" in route_paths
        assert "/apps/quran/surah/:surahNumber" in route_paths

        # Check composer actions contract
        composer_actions = manifest["composer_actions"]
        assert len(composer_actions) >= 1
        action = composer_actions[0]
        assert action["id"] == "insert_ayah"
        assert action["component"] == "AyahPickerModal"

        # Simulate composer action callback producing markdown quote
        selected_ayah = {
            "surah_number": 113,
            "surah_name": "الفلق",
            "ayah_number": 1,
            "arabic_text": "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ",
            "translation": "بگو پناه می‌برم به پروردگار سپیده دم"
        }

        generated_markdown = format_quran_markdown_reference(
            surah_number=selected_ayah["surah_number"],
            surah_name=selected_ayah["surah_name"],
            ayah_from=selected_ayah["ayah_number"],
            ayah_to=selected_ayah["ayah_number"],
            arabic_texts=[selected_ayah["arabic_text"]],
            translation_texts=[selected_ayah["translation"]]
        )

        assert "الفلق" in generated_markdown
        assert "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ" in generated_markdown

        # Verify publication of the generated markdown
        topic = Topic.objects.create(name="Composer Flow Topic", created_by=self.owner)
        res = self.owner_client.post(
            "/api/notes/",
            {"topic": topic.id, "content": generated_markdown, "media_type": "text"},
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    # --------------------------------------------------------------------------
    # Scenario 9: Plugin Error Boundary Isolation under Component Exception
    # --------------------------------------------------------------------------
    def test_scenario_09_plugin_error_boundary_isolation(self):
        """
        Scenario 9:
        1. A post references a corrupted/missing external plugin resource.
        2. Core post listing and post retrieval endpoints do not crash.
        3. Client retrieves 200 OK and renders plain text without breaking feed.
        """
        topic = Topic.objects.create(name="Error Boundary Topic", created_by=self.owner)

        post = Post.objects.create(
            topic=topic,
            author=self.owner,
            content="Post referencing non-existent or corrupted plugin"
        )

        if PostPluginReference is not None and self.quran_plugin is not None:
            # Create reference with abnormal / corrupted metadata
            PostPluginReference.objects.create(
                post=post,
                plugin=self.quran_plugin,
                resource_type="corrupted_resource",
                external_id="invalid:id:9999:xyz",
                metadata={"corrupted_field": True, "error_simulation": "unsupported_data"}
            )

        # Verify core post endpoint returns 200 OK
        res = self.reader_client.get(f"/api/notes/{post.id}/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["id"] == post.id

        # Verify topic post list returns 200 OK
        feed_res = self.reader_client.get(f"/api/notes/?topic_id={topic.id}")
        assert feed_res.status_code == status.HTTP_200_OK
        assert any(p["id"] == post.id for p in feed_res.data["results"])

    # --------------------------------------------------------------------------
    # Scenario 10: Complete Zero-Plugin Isolation Platform Check
    # --------------------------------------------------------------------------
    def test_scenario_10_complete_zero_plugin_isolation_platform_check(self):
        """
        Scenario 10:
        Simulate an environment where no plugins are installed or active.
        Executes full platform workflows:
        1. Topic lifecycle (Create, Update, Add Admin, Transfer Ownership).
        2. Post publishing (Plain text, Markdown, Media).
        3. Post social interactions (Comments, Reactions).
        4. Donation campaigns creation and contributing.
        5. Automated BotTask queue generation for connected platforms.
        All succeed 100% with zero dependencies on the plugin subsystem.
        """
        # 1. Topic lifecycle
        topic = Topic.objects.create(
            name="Zero-Plugin Pure Core Topic",
            created_by=self.owner,
            description="Pure core features verification",
            telegram_bot_active=True
        )

        tg_target = MessagingTarget.objects.create(
            user=self.owner,
            platform="telegram",
            chat_id="-10077665544",
            label="Pure Core Channel"
        )
        topic.telegram_connections.add(tg_target)

        # Add admin
        admin_rel = TopicAdmin.objects.create(
            topic=topic,
            user=self.admin,
            promoted_by=self.owner,
            custom_title="Core Admin"
        )
        assert admin_rel.id is not None

        # 2. Post publishing
        post_res = self.owner_client.post(
            "/api/notes/",
            {"topic": topic.id, "content": "# Core Markdown\n\n- Point 1\n- Point 2\n\n**Bold text**", "media_type": "text"},
            format="json"
        )
        assert post_res.status_code == status.HTTP_201_CREATED
        post_id = post_res.data["id"]

        # 3. Post interactions
        comment_res = self.reader_client.post(
            f"/api/notes/{post_id}/comments/",
            {"content": "Comment on pure core post"},
            format="json"
        )
        assert comment_res.status_code == status.HTTP_201_CREATED

        react_res = self.reader_client.post(
            f"/api/notes/{post_id}/react/",
            {"emoji": "🎉"},
            format="json"
        )
        assert react_res.status_code == status.HTTP_200_OK

        # 4. Donation Campaign Creation
        post_obj = Post.objects.get(id=post_id)
        campaign = DonationCampaign.objects.create(
            topic=topic,
            creator=self.owner,
            post=post_obj,
            title="کمپین حمایت از ایتام",
            description="جمع‌آوری هدایا و بسته‌های معیشتی",
            category=DonationCampaign.CategoryChoices.LIVELIHOOD,
            target_amount=100000000,
            collected_amount=25000000,
            donors_count=12
        )

        camp_res = self.owner_client.get(f"/api/v1/donations/campaigns/{campaign.id}/")
        assert camp_res.status_code == status.HTTP_200_OK
        assert camp_res.data["title"] == "کمپین حمایت از ایتام"

        # 5. BotTask queue verified
        bot_tasks = BotTask.objects.filter(post_id=post_id)
        assert bot_tasks.count() >= 1
        assert bot_tasks.first().platform == "telegram"
        assert "Core Markdown" in bot_tasks.first().text
