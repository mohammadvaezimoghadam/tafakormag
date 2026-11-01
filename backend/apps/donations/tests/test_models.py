from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.notes.models import Topic
from apps.donations.models import DonationCampaign, DonationTransaction, TransparencyLog, CampaignAttachment


class DonationModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='09121111111')
        self.topic = Topic.objects.create(name='خیریه و مهربانی', created_by=self.user)

    def test_minimum_target_amount_guard(self):
        """Ensure ValidationError is raised when target_amount < 100,000 Tomans."""
        campaign = DonationCampaign(
            topic=self.topic,
            creator=self.user,
            title='پویش درمان کودک بیمار',
            description='نیاز به تأمین داروهای خاص',
            target_amount=50000  # Below 100,000 Tomans minimum
        )
        with self.assertRaises(ValidationError):
            campaign.save()

    def test_valid_campaign_creation(self):
        """Ensure campaign creates successfully with valid target_amount >= 100,000."""
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.user,
            title='تأمین جهیزیه نوعروس',
            description='کمک به خانواده آبرومند',
            target_amount=15000000,
            category=DonationCampaign.CategoryChoices.DOWRY
        )
        self.assertIsNotNone(campaign.id)
        self.assertEqual(campaign.status, DonationCampaign.StatusChoices.ACTIVE)
        self.assertEqual(campaign.collected_amount, 0)
        self.assertEqual(campaign.donors_count, 0)

    def test_lifecycle_auto_update_completed(self):
        """Test that check_and_update_status() transitions from active to completed when collected_amount >= target_amount."""
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.user,
            title='آزادی زندانی جرایم غیرعمد',
            description='تأمین دیه',
            target_amount=10000000,
            collected_amount=10000000
        )
        campaign.check_and_update_status()
        self.assertEqual(campaign.status, DonationCampaign.StatusChoices.COMPLETED)

    def test_overfunding_lifecycle_auto_update(self):
        """Test that overfunding (collected_amount > target_amount) successfully transitions to completed."""
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.user,
            title='کمک به زلزله‌زدگان',
            description='تهیه چادر و مواد غذایی',
            target_amount=10000000,
            collected_amount=12500000
        )
        campaign.check_and_update_status()
        self.assertEqual(campaign.status, DonationCampaign.StatusChoices.COMPLETED)

    def test_deadline_expiry_guard(self):
        """Test that an overdue campaign transitions to expired."""
        past_time = timezone.now() - timedelta(days=2)
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.user,
            title='پویش بسته‌های تحصیلی مهر',
            description='خرید لوازم‌التحریر',
            target_amount=5000000,
            deadline=past_time
        )
        campaign.check_and_update_status()
        self.assertEqual(campaign.status, DonationCampaign.StatusChoices.EXPIRED)

    def test_transaction_minimum_amount_guard(self):
        """Ensure ValidationError is raised when transaction amount < 1000 Tomans."""
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.user,
            title='پویش تستی',
            description='توضیحات تستی',
            target_amount=1000000
        )
        trx = DonationTransaction(
            campaign=campaign,
            donor=self.user,
            amount=500  # Below 1,000 Tomans
        )
        with self.assertRaises(ValidationError):
            trx.save()
