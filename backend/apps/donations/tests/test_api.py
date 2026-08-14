from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from apps.accounts.models import User
from apps.notes.models import Topic, Post
from apps.donations.models import DonationCampaign, DonationTransaction, TransparencyLog
from apps.donations.services import verify_and_settle_transaction


class DonationAPITest(APITestCase):
    def setUp(self):
        self.creator = User.objects.create_user(phone='09121000001')
        self.creator.first_name = 'علی'
        self.creator.last_name = 'کریمی'
        self.creator.save()

        self.donor_user = User.objects.create_user(phone='09121000002')
        self.donor_user.first_name = 'محمد'
        self.donor_user.last_name = 'رضایی'
        self.donor_user.save()

        self.other_user = User.objects.create_user(phone='09121000003')
        self.other_user.first_name = 'سارا'
        self.other_user.last_name = 'امینی'
        self.other_user.save()

        self.topic = Topic.objects.create(name='تاپیک نیکوکاری', created_by=self.creator)

    def test_anonymous_privacy_masking(self):
        """
        Create a donation with is_anonymous=True. Fetch /campaigns/<id>/ and assert
        name == 'کاربر ناشناس' and avatar is None.
        """
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='کمک به درمان کودکان',
            description='خرید دارو',
            target_amount=10000000
        )
        trx = DonationTransaction.objects.create(
            campaign=campaign,
            donor=self.donor_user,
            amount=200000,
            is_anonymous=True,
            status=DonationTransaction.PaymentStatus.PENDING,
            authority='AUTH_ANON_1'
        )
        verify_and_settle_transaction(authority=trx.authority, gateway_ref='REF_ANON_1')

        response = self.client.get(f'/api/v1/donations/campaigns/{campaign.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        donors = response.data.get('donors', [])
        self.assertEqual(len(donors), 1)
        self.assertEqual(donors[0]['name'], 'کاربر ناشناس')
        self.assertIsNone(donors[0]['avatar'])
        self.assertTrue(donors[0]['is_anonymous'])

    def test_private_donors_list_guard(self):
        """
        Set is_public_donors_list=False. Fetch campaign and assert the donors array is [].
        """
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='پویش با لیست مخفی حامیان',
            description='شرح پویش',
            target_amount=5000000,
            is_public_donors_list=False
        )
        trx = DonationTransaction.objects.create(
            campaign=campaign,
            donor=self.donor_user,
            amount=100000,
            is_anonymous=False,
            status=DonationTransaction.PaymentStatus.PENDING,
            authority='AUTH_SECRET_1'
        )
        verify_and_settle_transaction(authority=trx.authority, gateway_ref='REF_SECRET_1')

        response = self.client.get(f'/api/v1/donations/campaigns/{campaign.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('donors'), [])

    def test_transparency_permission_guard(self):
        """
        Non-creator user posting to /transparency/ must receive 403 Forbidden.
        Campaign creator posting to /transparency/ must receive 201 Created.
        """
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='پویش تأمین جهیزیه',
            description='تأمین لوازم منزل',
            target_amount=30000000
        )

        # 1. Other user attempt -> 403 Forbidden
        self.client.force_authenticate(user=self.other_user)
        res_forbidden = self.client.post(f'/api/v1/donations/campaigns/{campaign.id}/transparency/', {
            'title': 'خرید یخچال',
            'description': 'فاکتور فروشگاه',
            'amount': 15000000
        })
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Creator attempt -> 201 Created
        self.client.force_authenticate(user=self.creator)
        res_success = self.client.post(f'/api/v1/donations/campaigns/{campaign.id}/transparency/', {
            'title': 'خرید یخچال و اجاق گاز',
            'description': 'فاکتور نمایندگی',
            'amount': 25000000
        })
        self.assertEqual(res_success.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_success.data['title'], 'خرید یخچال و اجاق گاز')

    def test_completed_campaign_donation_guard(self):
        """
        Attempting to initiate donation to an expired or completed campaign must receive 400 Bad Request.
        """
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='پویش تکمیل‌شده',
            description='پویش پایان‌یافته',
            target_amount=5000000,
            collected_amount=5000000,
            status=DonationCampaign.StatusChoices.COMPLETED
        )

        response = self.client.post(f'/api/v1/donations/campaigns/{campaign.id}/donate/', {
            'amount': 50000
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('پویش فعال نیست', str(response.data))

    def test_campaign_creation_atomic_with_topic_post(self):
        """
        Creating a campaign via API must atomically create both the DonationCampaign
        record and a corresponding post in the topic.
        """
        self.client.force_authenticate(user=self.creator)
        initial_posts_count = Post.objects.filter(topic=self.topic).count()

        payload = {
            'topic': self.topic.id,
            'title': 'پویش مدرسه‌سازی در مناطق محروم',
            'description': 'ساخت دو باب کلاس درس استاندارد',
            'category': 'education',
            'target_amount': 50000000,
            'is_public_donors_list': True
        }

        response = self.client.post('/api/v1/donations/campaigns/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], payload['title'])
        self.assertEqual(response.data['target_amount'], 50000000)

        # Assert post was automatically injected into topic
        final_posts_count = Post.objects.filter(topic=self.topic).count()
        self.assertEqual(final_posts_count, initial_posts_count + 1)

        last_post = Post.objects.filter(topic=self.topic).latest('created_at')
        self.assertIn('پویش مهربانی', last_post.content)
        self.assertIn(payload['title'], last_post.content)

    def test_campaign_update_by_creator(self):
        """
        Creators can update their own campaign details and topic post is synchronized.
        """
        self.client.force_authenticate(user=self.creator)
        campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.creator,
            title='عنوان اولیه پویش',
            description='توضیحات اولیه',
            target_amount=10000000,
            status=DonationCampaign.StatusChoices.ACTIVE
        )
        post = Post.objects.create(
            topic=self.topic,
            author=self.creator,
            content=f"🤲 **پویش مهربانی: {campaign.title}**\n\n{campaign.description}"
        )
        campaign.post = post
        campaign.save()

        update_payload = {
            'title': 'عنوان ویرایش‌شده پویش',
            'description': 'توضیحات جدید و به‌روزرسانی‌شده',
            'target_amount': 25000000
        }

        response = self.client.patch(f'/api/v1/donations/campaigns/{campaign.id}/', update_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'عنوان ویرایش‌شده پویش')
        self.assertEqual(response.data['target_amount'], 25000000)

        # Assert campaign in DB is updated
        campaign.refresh_from_db()
        self.assertEqual(campaign.title, 'عنوان ویرایش‌شده پویش')

        # Assert linked post content is synchronized
        post.refresh_from_db()
        self.assertIn('عنوان ویرایش‌شده پویش', post.content)
        self.assertIn('25,000,000', post.content)
