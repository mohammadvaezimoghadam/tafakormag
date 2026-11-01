"""
tests/e2e/conftest.py

E2E & Integration Test Fixtures and Harness for Tafakor Monorepo.
Provides:
1. DRF APIClient and user fixtures (api_client, auth_client, topic_admin_client, other_user_client).
2. Model factory fixtures (User, Topic, Post, TopicAdmin).
3. Quran seed data helpers (Surahs 1, 112, 113, 114 and editions: quran-simple, fa.ansarian, en.sahih).
4. Manifest generator fixtures for Plugin Validator and Registry testing.
5. Complete DB isolation & compatibility across pytest and Django test runners.
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Path & Django Environment Initialization
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

for path_str in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "note_platform.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

import django
from django.apps import apps
if not apps.ready:
    django.setup()

from django.contrib.auth import get_user_model
from django.db.backends.signals import connection_created
from django.dispatch import receiver
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apps.notes.models import Topic, Post, TopicAdmin, PostReaction, PostComment, BotTask

try:
    from apps.donations.models import DonationCampaign
except Exception:
    DonationCampaign = None

# Optional Plugin & Quran models (graceful fallback if not yet loaded)
try:
    from apps.plugin_system.models import (
        Plugin,
        PluginInstallation,
        PluginTopicInstallation,
        PostPluginReference,
    )
except Exception:
    Plugin = None
    PluginInstallation = None
    PluginTopicInstallation = None
    PostPluginReference = None

try:
    from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah, QuranJuz
except Exception:
    QuranEdition = None
    QuranSurah = None
    QuranAyah = None
    QuranJuz = None

User = get_user_model()


# ---------------------------------------------------------------------------
# SQLite Connection Signal Hook
# ---------------------------------------------------------------------------
@receiver(connection_created)
def configure_sqlite_pragmas(sender, connection, **kwargs):
    """Configures SQLite connections with WAL mode and 30s busy timeout."""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 30000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")


# ---------------------------------------------------------------------------
# SQLite Flush Command Guard
# ---------------------------------------------------------------------------
# When running on SQLite, Django's flush command triggers UNIQUE constraint
# collisions in django_content_type and locks the SQLite file across test runs.
# In PostgreSQL (production / container), flush operates normally.
try:
    import django.core.management.commands.flush
    _orig_flush_handle = django.core.management.commands.flush.Command.handle

    def _safe_flush_handle(self, *args, **options):
        from django.db import connections
        conn = connections[options.get("database", "default")]
        if conn.vendor == "sqlite":
            # On SQLite, pytest-django rolls back transactions cleanly.
            return
        return _orig_flush_handle(self, *args, **options)

    django.core.management.commands.flush.Command.handle = _safe_flush_handle
except Exception:
    pass


# ---------------------------------------------------------------------------
# Pytest Hooks & Configuration
# ---------------------------------------------------------------------------
def pytest_configure(config):
    """Register custom markers to avoid unknown marker warnings."""
    config.addinivalue_line("markers", "django_db: Mark test to run with Django DB access")
    config.addinivalue_line("markers", "tier1: Mark test as Tier 1 Feature Coverage")
    config.addinivalue_line("markers", "tier2: Mark test as Tier 2 Boundary & Edge Cases")
    config.addinivalue_line("markers", "tier3: Mark test as Tier 3 Pairwise Combinations")
    config.addinivalue_line("markers", "tier4: Mark test as Tier 4 Real-World Application Scenarios")
    config.addinivalue_line("markers", "non_regression: Mark test as Core Non-Regression check")


# ---------------------------------------------------------------------------
# Database Isolation Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clean_db(django_db_blocker):
    """
    Shadows root tests/conftest.py clean_db fixture for all tests in tests/e2e/.
    Rely on pytest-django transaction rollback to guarantee clean isolation on both
    SQLite and PostgreSQL without table locks or flush side-effects.
    """
    yield


# ---------------------------------------------------------------------------
# User & Authentication Client Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user_factory():
    """Factory fixture for creating test users with DRF tokens."""
    def _create_user(phone="09120000001", password="testpassword123", is_staff=False, is_superuser=False, **kwargs):
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={"is_staff": is_staff, "is_superuser": is_superuser, **kwargs}
        )
        if not created:
            user.set_password(password)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            for k, v in kwargs.items():
                setattr(user, k, v)
            user.save()
        else:
            user.set_password(password)
            user.save()
        Token.objects.get_or_create(user=user)
        return user
    return _create_user


@pytest.fixture
def auth_user(user_factory):
    """Primary authenticated test user."""
    return user_factory(phone="09121111111", password="testpassword123")


@pytest.fixture
def other_user(user_factory):
    """Secondary test user for permission and multi-user isolation tests."""
    return user_factory(phone="09122222222", password="testpassword456")


@pytest.fixture
def topic_admin_user(user_factory):
    """Test user intended to be assigned as Topic Admin."""
    return user_factory(phone="09123333333", password="testpassword789")


@pytest.fixture
def staff_user(user_factory):
    """Staff / admin user."""
    return user_factory(phone="09129999999", password="adminpassword", is_staff=True, is_superuser=True)


@pytest.fixture
def api_client():
    """Anonymous DRF APIClient."""
    return APIClient()


@pytest.fixture
def client_factory():
    """Factory creating an APIClient authenticated with a given user."""
    def _make_client(user=None):
        client = APIClient()
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
            client.force_authenticate(user=user)
        return client
    return _make_client


@pytest.fixture
def auth_client(client_factory, auth_user):
    """DRF APIClient authenticated as primary auth_user."""
    return client_factory(auth_user)


@pytest.fixture
def other_user_client(client_factory, other_user):
    """DRF APIClient authenticated as secondary other_user."""
    return client_factory(other_user)


@pytest.fixture
def topic_admin_client(client_factory, topic_admin_user):
    """DRF APIClient authenticated as topic_admin_user."""
    return client_factory(topic_admin_user)


# ---------------------------------------------------------------------------
# Core Model Fixtures (Topics, Posts, TopicAdmins)
# ---------------------------------------------------------------------------
@pytest.fixture
def topic_factory():
    """Factory creating Topic instances."""
    def _create_topic(name="E2E Test Topic", created_by=None, description="Topic for E2E tests", **kwargs):
        return Topic.objects.create(
            name=name,
            created_by=created_by,
            description=description,
            **kwargs
        )
    return _create_topic


@pytest.fixture
def test_topic(topic_factory, auth_user):
    """Standard test topic owned by auth_user."""
    return topic_factory(name="Primary E2E Topic", created_by=auth_user, description="E2E test topic description")


@pytest.fixture
def post_factory():
    """Factory creating Post instances."""
    def _create_post(topic, author, content="Standard E2E Post content", media_type="text", **kwargs):
        return Post.objects.create(
            topic=topic,
            author=author,
            content=content,
            media_type=media_type,
            **kwargs
        )
    return _create_post


@pytest.fixture
def test_post(post_factory, test_topic, auth_user):
    """Standard test post authored by auth_user in test_topic."""
    return post_factory(topic=test_topic, author=auth_user, content="This is an E2E test post.")


@pytest.fixture
def test_topic_admin(test_topic, topic_admin_user, auth_user):
    """TopicAdmin relationship assigning topic_admin_user as admin on test_topic."""
    return TopicAdmin.objects.create(
        topic=test_topic,
        user=topic_admin_user,
        promoted_by=auth_user,
        custom_title="Topic Moderator"
    )


# ---------------------------------------------------------------------------
# Quran Sample Seed Data & Fixtures
# ---------------------------------------------------------------------------
QURAN_SAMPLE_EDITIONS = [
    {
        "identifier": "quran-simple",
        "name": "Quran Simple (Arabic)",
        "language": "ar",
        "direction": "rtl",
        "type": "quran",
        "author": "Tanzil",
        "is_default": True
    },
    {
        "identifier": "fa.ansarian",
        "name": "ترجمه استاد انصاریان",
        "language": "fa",
        "direction": "rtl",
        "type": "translation",
        "author": "حسین انصاریان",
        "is_default": False
    },
    {
        "identifier": "en.sahih",
        "name": "Saheeh International",
        "language": "en",
        "direction": "ltr",
        "type": "translation",
        "author": "Saheeh International",
        "is_default": False
    }
]

QURAN_SAMPLE_SURAHS = [
    {
        "number": 1,
        "name_ar": "الفاتحة",
        "name_en": "Al-Fatihah",
        "name_fa": "فاتحه",
        "total_ayahs": 7,
        "revelation_type": "meccan",
        "bismillah_pre": False
    },
    {
        "number": 112,
        "name_ar": "الإخلاص",
        "name_en": "Al-Ikhlas",
        "name_fa": "توحید (اخلاص)",
        "total_ayahs": 4,
        "revelation_type": "meccan",
        "bismillah_pre": True
    },
    {
        "number": 113,
        "name_ar": "الفلق",
        "name_en": "Al-Falaq",
        "name_fa": "فلق",
        "total_ayahs": 5,
        "revelation_type": "meccan",
        "bismillah_pre": True
    },
    {
        "number": 114,
        "name_ar": "الناس",
        "name_en": "An-Nas",
        "name_fa": "ناس",
        "total_ayahs": 6,
        "revelation_type": "meccan",
        "bismillah_pre": True
    }
]

QURAN_SAMPLE_JUZS = [
    {
        "number": 1,
        "name": "الم",
        "start_surah": 1,
        "start_ayah": 1,
        "end_surah": 2,
        "end_ayah": 141
    },
    {
        "number": 30,
        "name": "عم",
        "start_surah": 78,
        "start_ayah": 1,
        "end_surah": 114,
        "end_ayah": 6
    }
]

QURAN_SAMPLE_AYAHS = [
    # --- Surah 1: Al-Fatihah (1..7) ---
    {
        "surah_number": 1, "ayah_number": 1, "juz_number": 1,
        "texts": {
            "quran-simple": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "fa.ansarian": "به نام خداوند بخشنده مهربان",
            "en.sahih": "In the name of Allah, the Entirely Merciful, the Especially Merciful."
        }
    },
    {
        "surah_number": 1, "ayah_number": 2, "juz_number": 1,
        "texts": {
            "quran-simple": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
            "fa.ansarian": "ستایش مخصوص خدایی است که پروردگار جهانیان است.",
            "en.sahih": "[All] praise is [due] to Allah, Lord of the worlds -"
        }
    },
    {
        "surah_number": 1, "ayah_number": 3, "juz_number": 1,
        "texts": {
            "quran-simple": "الرَّحْمَٰنِ الرَّحِيمِ",
            "fa.ansarian": "بخشنده و مهربان است.",
            "en.sahih": "The Entirely Merciful, the Especially Merciful,"
        }
    },
    {
        "surah_number": 1, "ayah_number": 4, "juz_number": 1,
        "texts": {
            "quran-simple": "مَالِكِ يَوْمِ الدِّينِ",
            "fa.ansarian": "مالک و فرمانروای روز جزاست.",
            "en.sahih": "Sovereign of the Day of Recompense."
        }
    },
    {
        "surah_number": 1, "ayah_number": 5, "juz_number": 1,
        "texts": {
            "quran-simple": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
            "fa.ansarian": "تنها تو را می‌پرستیم و تنها از تو یاری می‌جوییم.",
            "en.sahih": "It is You we worship and You we ask for help."
        }
    },
    {
        "surah_number": 1, "ayah_number": 6, "juz_number": 1,
        "texts": {
            "quran-simple": "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ",
            "fa.ansarian": "ما را به راه راست هدایت فرما،",
            "en.sahih": "Guide us to the straight path -"
        }
    },
    {
        "surah_number": 1, "ayah_number": 7, "juz_number": 1,
        "texts": {
            "quran-simple": "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
            "fa.ansarian": "راه کسانی که به آنان نعمت دادی، نه آنان که مورد غضب واقع شدند و نه گمراهان.",
            "en.sahih": "The path of those upon whom You have bestowed favor, not of those who have evoked [Your] anger or of those who are astray."
        }
    },
    # --- Surah 112: Al-Ikhlas (1..4) ---
    {
        "surah_number": 112, "ayah_number": 1, "juz_number": 30,
        "texts": {
            "quran-simple": "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "fa.ansarian": "بگو: او خدای یکتاست؛",
            "en.sahih": "Say, 'He is Allah, [who is] One,"
        }
    },
    {
        "surah_number": 112, "ayah_number": 2, "juz_number": 30,
        "texts": {
            "quran-simple": "اللَّهُ الصَّمَدُ",
            "fa.ansarian": "خدای بی نیاز که همه نیازمندان قصد او می کنند؛",
            "en.sahih": "Allah, the Eternal Refuge."
        }
    },
    {
        "surah_number": 112, "ayah_number": 3, "juz_number": 30,
        "texts": {
            "quran-simple": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
            "fa.ansarian": "نزاده و زاده نشده است،",
            "en.sahih": "He neither begets nor is born,"
        }
    },
    {
        "surah_number": 112, "ayah_number": 4, "juz_number": 30,
        "texts": {
            "quran-simple": "وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ",
            "fa.ansarian": "و برای او هیچ همتا و معادلی نبوده است.",
            "en.sahih": "Nor is there to Him any equivalent.'"
        }
    },
    # --- Surah 113: Al-Falaq (1..5) ---
    {
        "surah_number": 113, "ayah_number": 1, "juz_number": 30,
        "texts": {
            "quran-simple": "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ",
            "fa.ansarian": "بگو: پناه می‌برم به پروردگار سپیده دم،",
            "en.sahih": "Say, 'I seek refuge in the Lord of daybreak"
        }
    },
    {
        "surah_number": 113, "ayah_number": 2, "juz_number": 30,
        "texts": {
            "quran-simple": "مِنْ شَرِّ مَا خَلَقَ",
            "fa.ansarian": "از شر آنچه آفریده است،",
            "en.sahih": "From the evil of that which He created"
        }
    },
    {
        "surah_number": 113, "ayah_number": 3, "juz_number": 30,
        "texts": {
            "quran-simple": "وَمِنْ شَرِّ غَاسِقٍ إِذَا وَقَبَ",
            "fa.ansarian": "و از شر تاریکی شب هنگامی که فرا رسد،",
            "en.sahih": "And from the evil of darkness when it settles"
        }
    },
    {
        "surah_number": 113, "ayah_number": 4, "juz_number": 30,
        "texts": {
            "quran-simple": "وَمِنْ شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ",
            "fa.ansarian": "و از شر زنان دمنده در گره‌ها،",
            "en.sahih": "And from the evil of the blowers in knots"
        }
    },
    {
        "surah_number": 113, "ayah_number": 5, "juz_number": 30,
        "texts": {
            "quran-simple": "وَمِنْ شَرِّ حَاسِدٍ إِذَا حَسَدَ",
            "fa.ansarian": "و از شر حسود هنگامی که حسد می‌ورزد.",
            "en.sahih": "And from the evil of an envier when he envies.'"
        }
    },
    # --- Surah 114: An-Nas (1..6) ---
    {
        "surah_number": 114, "ayah_number": 1, "juz_number": 30,
        "texts": {
            "quran-simple": "قُلْ أَعُوذُ بِرَبِّ النَّاسِ",
            "fa.ansarian": "بگو: پناه می‌برم به پروردگار مردم،",
            "en.sahih": "Say, 'I seek refuge in the Lord of mankind,"
        }
    },
    {
        "surah_number": 114, "ayah_number": 2, "juz_number": 30,
        "texts": {
            "quran-simple": "مَلِكِ النَّاسِ",
            "fa.ansarian": "پادشاه و فرمانروای مردم،",
            "en.sahih": "The Sovereign of mankind,"
        }
    },
    {
        "surah_number": 114, "ayah_number": 3, "juz_number": 30,
        "texts": {
            "quran-simple": "إِلَٰهِ النَّاسِ",
            "fa.ansarian": "معبود و یکتای مردم،",
            "en.sahih": "The God of mankind,"
        }
    },
    {
        "surah_number": 114, "ayah_number": 4, "juz_number": 30,
        "texts": {
            "quran-simple": "مِنْ شَرِّ الْوَسْوَاسِ الْخَنَّاسِ",
            "fa.ansarian": "از شر وسوسه‌گر نهان‌کار،",
            "en.sahih": "From the evil of the retreating whisperer -"
        }
    },
    {
        "surah_number": 114, "ayah_number": 5, "juz_number": 30,
        "texts": {
            "quran-simple": "الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ",
            "fa.ansarian": "آنکه همواره در سینه‌های مردم وسوسه می‌کند،",
            "en.sahih": "Who whispers into the breasts of mankind -"
        }
    },
    {
        "surah_number": 114, "ayah_number": 6, "juz_number": 30,
        "texts": {
            "quran-simple": "مِنَ الْجِنَّةِ وَالنَّاسِ",
            "fa.ansarian": "چه از جن باشد و چه از انس.",
            "en.sahih": "From among the jinn and mankind.'"
        }
    }
]


@pytest.fixture
def quran_sample_editions_data():
    """Returns sample edition definitions for Quran tests."""
    return QURAN_SAMPLE_EDITIONS


@pytest.fixture
def quran_sample_surahs_data():
    """Returns sample surah definitions (1, 112, 113, 114)."""
    return QURAN_SAMPLE_SURAHS


@pytest.fixture
def quran_sample_juzs_data():
    """Returns sample Juz definitions (1, 30)."""
    return QURAN_SAMPLE_JUZS


@pytest.fixture
def quran_sample_ayahs_data():
    """Returns sample ayahs with translations across editions."""
    return QURAN_SAMPLE_AYAHS


@pytest.fixture
def quran_sample_full_dataset():
    """
    Returns a consolidated Quran JSON dataset suitable for testing
    importers, search indexers, and navigation APIs.
    """
    return {
        "version": "1.0",
        "editions": QURAN_SAMPLE_EDITIONS,
        "juzs": QURAN_SAMPLE_JUZS,
        "surahs": QURAN_SAMPLE_SURAHS,
        "ayahs": QURAN_SAMPLE_AYAHS
    }


@pytest.fixture
def seed_quran_db(quran_sample_full_dataset):
    """
    Helper fixture that seeds the SQLite/PostgreSQL test database with
    sample Quran models using exact Django model field signatures.
    """
    if QuranEdition is None or QuranSurah is None or QuranAyah is None:
        return {"seeded": False, "reason": "Quran models not yet loaded"}

    editions = {}
    for ed in quran_sample_full_dataset["editions"]:
        obj, _ = QuranEdition.objects.get_or_create(
            identifier=ed["identifier"],
            defaults={
                "name": ed["name"],
                "english_name": ed.get("name", ""),
                "language": ed["language"],
                "direction": ed["direction"],
                "type": ed.get("type", "quran"),
                "author": ed.get("author", ""),
                "is_default": ed.get("is_default", False),
                "total_ayahs": 6236,
            }
        )
        editions[ed["identifier"]] = obj

    surahs = {}
    for sr in quran_sample_full_dataset["surahs"]:
        obj, _ = QuranSurah.objects.get_or_create(
            number=sr["number"],
            defaults={
                "name": sr["name_ar"],
                "english_name": sr["name_en"],
                "english_name_translation": sr.get("name_fa", ""),
                "ayah_count": sr["total_ayahs"],
                "revelation_type": sr.get("revelation_type", "Meccan").capitalize(),
                "bismillah_pre": sr.get("bismillah_pre", True),
                "juz_start": 1 if sr["number"] <= 1 else 30,
            }
        )
        surahs[sr["number"]] = obj

    juzs = {}
    if QuranJuz is not None:
        for jz in quran_sample_full_dataset["juzs"]:
            s_surah = surahs.get(jz["start_surah"])
            e_surah = surahs.get(jz["end_surah"])
            if s_surah and e_surah:
                obj, _ = QuranJuz.objects.get_or_create(
                    number=jz["number"],
                    defaults={
                        "name": jz["name"],
                        "start_surah": s_surah,
                        "start_ayah": jz["start_ayah"],
                        "end_surah": e_surah,
                        "end_ayah": jz["end_ayah"],
                    }
                )
                juzs[jz["number"]] = obj

    # Ayahs
    ayah_objs = []
    global_ayah_counter = 1
    for ay in quran_sample_full_dataset["ayahs"]:
        surah_obj = surahs.get(ay["surah_number"])
        juz_num = ay.get("juz_number", 1)
        for ed_id, text in ay["texts"].items():
            edition_obj = editions.get(ed_id)
            if surah_obj and edition_obj:
                ayah_obj, _ = QuranAyah.objects.get_or_create(
                    edition=edition_obj,
                    surah=surah_obj,
                    number_in_surah=ay["ayah_number"],
                    defaults={
                        "number": global_ayah_counter,
                        "text": text,
                        "normalized_text": text,
                        "juz": juz_num,
                    }
                )
                ayah_objs.append(ayah_obj)
        global_ayah_counter += 1

    return {
        "seeded": True,
        "editions": editions,
        "surahs": surahs,
        "juzs": juzs,
        "ayah_count": len(ayah_objs),
    }


# ---------------------------------------------------------------------------
# Plugin System Manifest & Generator Fixtures
# ---------------------------------------------------------------------------
SAMPLE_MANIFEST_BASE = {
    "manifest_version": 1,
    "identifier": "quran",
    "name": "Quran Reader & Search",
    "name_fa": "قرآن کریم و جستجو",
    "version": "1.0.0",
    "description": "Official Quran plugin for Tafakor with multi-edition support and cross-DB search.",
    "author": "Tafakor Core Team",
    "capabilities": ["reader", "search", "composer_action", "navigation"],
    "scopes": ["read:content", "write:composer"],
    "settings_schema": {
        "type": "object",
        "properties": {
            "default_edition": {"type": "string", "default": "quran-simple"},
            "default_translation": {"type": "string", "default": "fa.ansarian"},
            "font_size": {"type": "integer", "default": 18}
        }
    },
    "routes": [
        {"path": "/apps/quran", "component": "QuranIndexView", "name": "quran-index"},
        {"path": "/apps/quran/surah/:surahNumber", "component": "SurahDetailView", "name": "quran-surah"}
    ],
    "composer_actions": [
        {
            "id": "insert_ayah",
            "title": "درج آیه قرآن",
            "icon": "book-open",
            "component": "AyahPickerModal"
        }
    ]
}


def make_plugin_manifest(identifier="custom_plugin", name="Custom Plugin", version="1.0.0", **overrides):
    """Helper to construct a valid plugin manifest dictionary with optional overrides."""
    manifest = dict(SAMPLE_MANIFEST_BASE)
    manifest["identifier"] = identifier
    manifest["name"] = name
    manifest["version"] = version
    manifest.update(overrides)
    return manifest


def make_invalid_manifest(case_type="missing_version", **overrides):
    """Helper to construct various malformed manifest dictionaries for testing."""
    if case_type == "missing_version":
        m = make_plugin_manifest(**overrides)
        m.pop("manifest_version", None)
        return m
    elif case_type == "unsupported_manifest_version":
        return make_plugin_manifest(manifest_version=99, **overrides)
    elif case_type == "invalid_identifier":
        return make_plugin_manifest(identifier="Invalid Identifier With Spaces!", **overrides)
    elif case_type == "empty_identifier":
        return make_plugin_manifest(identifier="", **overrides)
    elif case_type == "missing_name":
        m = make_plugin_manifest(**overrides)
        m.pop("name", None)
        return m
    elif case_type == "invalid_capabilities":
        return make_plugin_manifest(capabilities="not-a-list", **overrides)
    elif case_type == "invalid_scopes":
        return make_plugin_manifest(scopes=["invalid:scope:format:excessive"], **overrides)
    elif case_type == "invalid_semver":
        return make_plugin_manifest(version="v1_beta_final", **overrides)
    elif case_type == "malformed_schema":
        return make_plugin_manifest(settings_schema="invalid_json_schema", **overrides)
    elif case_type == "empty_manifest":
        return {}
    else:
        return {"corrupted": True}


@pytest.fixture
def sample_plugin_manifest():
    """Returns a copy of a standard valid plugin manifest dict."""
    return dict(SAMPLE_MANIFEST_BASE)


@pytest.fixture
def plugin_manifest_factory():
    """
    Factory creating customized plugin manifest dictionaries.
    Supports overrides for testing validation, edge cases, and registry features.
    """
    return make_plugin_manifest


@pytest.fixture
def invalid_manifest_factory():
    """
    Factory creating intentionally malformed or invalid manifests
    for adversarial and boundary testing of ManifestValidator.
    """
    return make_invalid_manifest


@pytest.fixture
def temp_manifest_file():
    """
    Fixture that writes a given manifest dict to a temporary JSON file,
    providing its path and cleaning up afterwards.
    """
    created_files = []

    def _write_file(manifest_data):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(manifest_data, tmp, ensure_ascii=False, indent=2)
        tmp.close()
        created_files.append(tmp.name)
        return tmp.name

    yield _write_file

    for f_path in created_files:
        try:
            if os.path.exists(f_path):
                os.remove(f_path)
        except OSError:
            pass
