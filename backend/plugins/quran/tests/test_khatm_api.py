"""
Unit and integration tests for Quran Khatm System (Group Campaigns, Slots, Offline Sync, and Web Preview).
"""
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from plugins.quran.models import (
    KhatmCategory,
    KhatmCampaign,
    KhatmSlot,
    PersonalKhatmPlan,
    QuranSurah,
)
from plugins.quran.services.khatm_service import release_expired_khatm_slots

User = get_user_model()


class KhatmApiTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(phone="09121111111", first_name="Ali", last_name="Rezaei")
        self.user2 = User.objects.create(phone="09122222222", first_name="Sara", last_name="Ahmadi")

        self.category = KhatmCategory.objects.create(
            title="سلامتی و فرج",
            slug="faraj",
            icon="heart",
            display_order=1
        )

        self.surah1 = QuranSurah.objects.create(
            number=1,
            name="الفاتحة",
            english_name="Al-Faatiha",
            english_name_translation="The Opening",
            revelation_type="Meccan",
            ayah_count=7,
            order_of_revelation=5,
            page_start=1,
            page_end=1,
            juz_start=1,
            bismillah_pre=False
        )

    def test_khatm_category_list(self):
        url = reverse('quran-khatm-categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['slug'], 'faraj')

    def test_create_juz_campaign_auto_creates_30_slots(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('quran-khatm-campaign-list')
        payload = {
            "title": "ختم قرآن ماه رمضان",
            "description": "هدیه به اموات",
            "unit_type": "juz",
            "category_id": self.category.id,
            "is_public": True
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "ختم قرآن ماه رمضان")
        self.assertEqual(response.data['target_units'], 30)
        self.assertEqual(len(response.data['slots']), 30)
        self.assertTrue(response.data['invite_code'])

        # Verify in DB
        campaign = KhatmCampaign.objects.get(invite_code=response.data['invite_code'])
        self.assertEqual(campaign.slots.count(), 30)
        self.assertEqual(campaign.slots.filter(status=KhatmSlot.Status.AVAILABLE).count(), 30)

    def test_reserve_and_complete_juz_slot(self):
        # Create campaign
        campaign = KhatmCampaign.objects.create(
            creator=self.user1,
            title="ختم سی جزء",
            unit_type=KhatmCampaign.UnitType.JUZ,
            target_units=30
        )
        for i in range(1, 31):
            KhatmSlot.objects.create(
                campaign=campaign,
                unit_number=i,
                quantity=1,
                status=KhatmSlot.Status.AVAILABLE
            )

        # User 2 reserves Juz 7
        self.client.force_authenticate(user=self.user2)
        reserve_url = reverse('quran-khatm-campaign-reserve', kwargs={'invite_code': campaign.invite_code})
        res = self.client.post(reserve_url, {"unit_number": 7}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['slot']['unit_number'], 7)
        self.assertEqual(res.data['slot']['status'], 'reserved')
        self.assertTrue(res.data['slot']['is_mine'])

        campaign.refresh_from_db()
        self.assertEqual(campaign.reserved_units, 1)
        self.assertEqual(campaign.completed_units, 0)

        # User 2 completes Juz 7
        complete_url = reverse('quran-khatm-campaign-complete', kwargs={'invite_code': campaign.invite_code})
        comp_res = self.client.post(complete_url, {"unit_number": 7}, format='json')
        self.assertEqual(comp_res.status_code, status.HTTP_200_OK)
        self.assertEqual(comp_res.data['slot']['status'], 'completed')

        campaign.refresh_from_db()
        self.assertEqual(campaign.reserved_units, 0)
        self.assertEqual(campaign.completed_units, 1)

    def test_voluntary_release_slot(self):
        campaign = KhatmCampaign.objects.create(
            creator=self.user1,
            title="ختم تستی",
            unit_type=KhatmCampaign.UnitType.JUZ,
            target_units=30,
            reserved_units=1
        )
        slot = KhatmSlot.objects.create(
            campaign=campaign,
            unit_number=5,
            quantity=1,
            status=KhatmSlot.Status.RESERVED,
            user=self.user2,
            reserved_at=timezone.now()
        )

        self.client.force_authenticate(user=self.user2)
        release_url = reverse('quran-khatm-campaign-release', kwargs={'invite_code': campaign.invite_code})
        res = self.client.post(release_url, {"slot_id": slot.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        slot.refresh_from_db()
        self.assertEqual(slot.status, KhatmSlot.Status.AVAILABLE)
        self.assertIsNone(slot.user)

        campaign.refresh_from_db()
        self.assertEqual(campaign.reserved_units, 0)

    def test_expired_slots_released_by_service(self):
        past_time = timezone.now() - timedelta(hours=50)
        campaign = KhatmCampaign.objects.create(
            creator=self.user1,
            title="ختم منقضی‌شده",
            unit_type=KhatmCampaign.UnitType.JUZ,
            target_units=30,
            reserved_units=1
        )
        slot = KhatmSlot.objects.create(
            campaign=campaign,
            unit_number=12,
            quantity=1,
            status=KhatmSlot.Status.RESERVED,
            user=self.user2,
            reserved_at=past_time,
            expires_at=past_time + timedelta(hours=48)  # expired 2 hours ago
        )

        released = release_expired_khatm_slots()
        self.assertEqual(released, 1)

        slot.refresh_from_db()
        self.assertEqual(slot.status, KhatmSlot.Status.AVAILABLE)
        self.assertIsNone(slot.user)

        campaign.refresh_from_db()
        self.assertEqual(campaign.reserved_units, 0)

    def test_personal_khatm_sync_last_write_wins(self):
        self.client.force_authenticate(user=self.user1)
        sync_url = reverse('quran-personal-khatms-sync')

        t1 = timezone.now() - timedelta(minutes=10)
        t2 = timezone.now()

        # Step 1: Client syncs first version
        payload = {
            "plans": [
                {
                    "client_id": "test-uuid-1",
                    "title": "ختم روزانه جزء ۳۰",
                    "unit_type": "juz",
                    "range_from": 30,
                    "range_to": 30,
                    "planning_mode": "bySessionCount",
                    "session_count": 30,
                    "quota_per_session": 1,
                    "cadence": "daily",
                    "start_date": "2026-03-01",
                    "end_date": "2026-03-30",
                    "sessions_progress": [],
                    "completed_sessions": 5,
                    "client_updated_at": t1.isoformat()
                }
            ]
        }
        res1 = self.client.post(sync_url, payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(PersonalKhatmPlan.objects.filter(user=self.user1).count(), 1)
        plan = PersonalKhatmPlan.objects.get(client_id="test-uuid-1")
        self.assertEqual(plan.completed_sessions, 5)

        # Step 2: Client syncs newer version (t2 > t1) -> should update
        payload2 = {
            "plans": [
                {
                    "client_id": "test-uuid-1",
                    "title": "ختم روزانه جزء ۳۰",
                    "unit_type": "juz",
                    "range_from": 30,
                    "range_to": 30,
                    "planning_mode": "bySessionCount",
                    "session_count": 30,
                    "quota_per_session": 1,
                    "cadence": "daily",
                    "start_date": "2026-03-01",
                    "end_date": "2026-03-30",
                    "sessions_progress": [],
                    "completed_sessions": 10,
                    "client_updated_at": t2.isoformat()
                }
            ]
        }
        res2 = self.client.post(sync_url, payload2, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        plan.refresh_from_db()
        self.assertEqual(plan.completed_sessions, 10)

        # Step 3: Stale request arriving late (t1 < t2) -> must NOT overwrite
        payload_stale = {
            "plans": [
                {
                    "client_id": "test-uuid-1",
                    "title": "ختم روزانه جزء ۳۰",
                    "unit_type": "juz",
                    "range_from": 30,
                    "range_to": 30,
                    "planning_mode": "bySessionCount",
                    "session_count": 30,
                    "quota_per_session": 1,
                    "cadence": "daily",
                    "start_date": "2026-03-01",
                    "end_date": "2026-03-30",
                    "sessions_progress": [],
                    "completed_sessions": 3,
                    "client_updated_at": t1.isoformat()
                }
            ]
        }
        res3 = self.client.post(sync_url, payload_stale, format='json')
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        plan.refresh_from_db()
        self.assertEqual(plan.completed_sessions, 10)  # Preserved newer data!

    def test_khatm_web_preview_renders_html_and_open_graph(self):
        campaign = KhatmCampaign.objects.create(
            creator=self.user1,
            title="ختم سوره یس برای اموات",
            description="هدیه به شهدای گمنام",
            unit_type=KhatmCampaign.UnitType.SURAH,
            target_surah=self.surah1,
            target_units=100,
            completed_units=40,
            reserved_units=10
        )

        url = f"/k/{campaign.invite_code}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn("ختم سوره یس برای اموات", content)
        self.assertIn('property="og:title"', content)
        self.assertIn(f"tafakor://quran/khatm/{campaign.invite_code}", content)
