from concurrent.futures import ThreadPoolExecutor
from django.test import TransactionTestCase
from django.db import connection
from apps.accounts.models import User
from apps.notes.models import Topic
from apps.donations.models import DonationCampaign, DonationTransaction
from apps.donations.services import initiate_donation, verify_and_settle_transaction


class DonationServicesTest(TransactionTestCase):
    def setUp(self):
        self.creator = User.objects.create_user(phone='09122222222')
        self.donor1 = User.objects.create_user(phone='09123333333')
        self.donor2 = User.objects.create_user(phone='09124444444')
        self.topic = Topic.objects.create(name='خیریه عمومی', created_by=self.creator)

    def test_initiate_donation_success(self):
        """Test initiating donation returns pending transaction and authority."""
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='درمان بیمار نیازمند',
            description='کمک درمانی',
            target_amount=10000000
        )
        trx, gateway_url = initiate_donation(
            campaign_id=campaign.id,
            amount=250000,
            is_anonymous=False,
            donor=self.donor1
        )
        self.assertIsNotNone(trx.id)
        self.assertEqual(trx.status, DonationTransaction.PaymentStatus.PENDING)
        self.assertEqual(trx.amount, 250000)
        self.assertTrue(trx.authority.startswith('AUTH_'))
        self.assertIn('authority=', gateway_url)

    def test_idempotent_settlement(self):
        """
        Idempotent Settle: Call verify_and_settle_transaction() multiple times with the same
        authority and assert that collected_amount and donors_count increase only once.
        """
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='پویش آزادی زندانیان',
            description='شرح پویش',
            target_amount=50000000
        )
        trx, _ = initiate_donation(
            campaign_id=campaign.id,
            amount=500000,
            donor=self.donor1
        )

        # First settlement
        res1 = verify_and_settle_transaction(authority=trx.authority, gateway_ref='REF_001')
        self.assertEqual(res1.status, DonationTransaction.PaymentStatus.SUCCESSFUL)

        campaign.refresh_from_db()
        self.assertEqual(campaign.collected_amount, 500000)
        self.assertEqual(campaign.donors_count, 1)

        # Second settlement (duplicate callback simulation)
        res2 = verify_and_settle_transaction(authority=trx.authority, gateway_ref='REF_001_DUPLICATE')
        self.assertEqual(res2.status, DonationTransaction.PaymentStatus.SUCCESSFUL)

        campaign.refresh_from_db()
        self.assertEqual(campaign.collected_amount, 500000)
        self.assertEqual(campaign.donors_count, 1)

    def test_concurrent_donations_simulation(self):
        """
        Simulate settlement of multiple distinct transactions and verify that the final
        collected_amount and donors_count match the exact sum without race conditions.
        """
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='پویش همزمان تست ریس کاندیشن',
            description='تست قفل سطری و اتمیسیتی',
            target_amount=20000000
        )

        num_transactions = 10
        donation_amount = 50000  # 50,000 Tomans each
        authorities = []

        for i in range(num_transactions):
            trx, _ = initiate_donation(
                campaign_id=campaign.id,
                amount=donation_amount,
                donor=self.donor1
            )
            authorities.append(trx.authority)

        def settle_worker(auth):
            return verify_and_settle_transaction(authority=auth, gateway_ref=f"REF_{auth[:8]}")

        if connection.vendor == 'sqlite':
            # SQLite uses whole-database locking in threads; on PostgreSQL row-level select_for_update works across threads
            results = [settle_worker(auth) for auth in authorities]
        else:
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(settle_worker, authorities))

        self.assertEqual(len(results), num_transactions)
        for r in results:
            self.assertEqual(r.status, DonationTransaction.PaymentStatus.SUCCESSFUL)

        campaign.refresh_from_db()
        expected_total = num_transactions * donation_amount
        self.assertEqual(campaign.collected_amount, expected_total)
        self.assertEqual(campaign.donors_count, num_transactions)
