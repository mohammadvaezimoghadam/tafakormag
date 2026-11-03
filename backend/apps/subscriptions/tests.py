from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.subscriptions.models import SubscriptionPlan, UserSubscription, PurchaseVerificationLog
from apps.subscriptions.utils import has_active_subscription, invalidate_user_subscription_cache

User = get_user_model()


class SubscriptionSystemTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpassword123'
        )
        self.user2 = User.objects.create_user(
            phone='09987654321',
            password='testpassword123'
        )

        # ایجاد پلن‌های تستی
        self.plan_1m = SubscriptionPlan.objects.create(
            plugin_identifier='quran',
            sku='sub_vip_1m',
            title='اشتراک ۱ ماهه قرآن',
            duration_days=30,
            price=390000,
            is_active=True
        )
        self.plan_3m = SubscriptionPlan.objects.create(
            plugin_identifier='quran',
            sku='sub_vip_3m',
            title='اشتراک ۳ ماهه قرآن',
            duration_days=90,
            price=890000,
            is_active=True
        )

        invalidate_user_subscription_cache(self.user.id)
        invalidate_user_subscription_cache(self.user2.id)

    def test_get_subscription_plans(self):
        """تست اندپوینت دریافت لیست پلن‌ها"""
        url = '/api/subscriptions/plans/?plugin=quran'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['sku'], 'sub_vip_1m')
        self.assertEqual(data[0]['price_toman'], 39000)

    def test_verify_purchase_success(self):
        """تست خرید موفق اشتراک با توکن تستی"""
        self.client.force_authenticate(user=self.user)
        url = '/api/subscriptions/verify/'
        payload = {
            'sku': 'sub_vip_1m',
            'purchase_token': 'mock_token_abc_123',
            'marketplace': 'cafebazaar',
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['subscription']['has_active_subscription'])
        self.assertEqual(data['subscription']['remaining_days'], 30)

        # بررسی در دیتابیس
        self.assertTrue(has_active_subscription(self.user, 'quran'))
        self.assertFalse(has_active_subscription(self.user2, 'quran'))
        self.assertTrue(PurchaseVerificationLog.objects.filter(purchase_token='mock_token_abc_123', is_verified=True).exists())

    def test_replay_attack_prevention(self):
        """تست جلوگیری قطعی از سوءاستفاده از توکن تکراری"""
        self.client.force_authenticate(user=self.user)
        url = '/api/subscriptions/verify/'
        payload = {
            'sku': 'sub_vip_1m',
            'purchase_token': 'mock_token_single_use_999',
        }
        # بار اول موفق
        res1 = self.client.post(url, data=payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # بار دوم با همان توکن توسط کاربر دیگر
        self.client.force_authenticate(user=self.user2)
        res2 = self.client.post(url, data=payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('purchase_token', str(res2.json()))

    def test_subscription_renewal_extends_duration(self):
        """تست تمدید هوشمند: افزودن روزهای جدید به انتهای اعتبار قبلی"""
        self.client.force_authenticate(user=self.user)
        url = '/api/subscriptions/verify/'

        # خرید پلن ۱ ماهه (۳۰ روز)
        self.client.post(url, data={'sku': 'sub_vip_1m', 'purchase_token': 'token_step_1'}, format='json')

        # خرید پلن ۳ ماهه بلافاصله پس از آن (۹۰ روز دیگر)
        res = self.client.post(url, data={'sku': 'sub_vip_3m', 'purchase_token': 'token_step_2'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()

        # مجموع اعتبار باید حدود ۱۲۰ روز باشد
        self.assertGreaterEqual(data['subscription']['remaining_days'], 119)

    def test_user_subscription_status_endpoint(self):
        """تست استعلام وضعیت اشتراک کاربر جاری"""
        self.client.force_authenticate(user=self.user)
        url = '/api/subscriptions/my-status/?plugin=quran'

        # قبل از خرید: فاقد اشتراک
        res_before = self.client.get(url)
        self.assertEqual(res_before.status_code, status.HTTP_200_OK)
        self.assertFalse(res_before.json()['has_active_subscription'])

        # بعد از خرید
        self.client.post('/api/subscriptions/verify/', data={'sku': 'sub_vip_1m', 'purchase_token': 'mock_token_status_test'}, format='json')
        res_after = self.client.get(url)
        self.assertEqual(res_after.status_code, status.HTTP_200_OK)
        self.assertTrue(res_after.json()['has_active_subscription'])
        self.assertEqual(res_after.json()['plan_title'], 'اشتراک ۱ ماهه قرآن')

