from django.test import TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock
import requests

from apps.accounts.services import (
    SMSDeliveryError,
    kavenegar_configured,
    send_otp_sms,
)

class AccountsServicesTestCase(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.accounts.services.kavenegar_configured", return_value=True)
    @override_settings(KAVENEGAR_API_KEY="test_key", KAVENEGAR_SENDER="test_sender")
    @patch("requests.post")
    def test_send_otp_sms_success(self, mock_post, mock_configured):
        mock_response = MagicMock()
        mock_response.content = b'{"return":{"status":200,"message":"success"},"entries":[]}'
        mock_post.return_value = mock_response

        # نباید هیچ خطایی پرتاب شود
        send_otp_sms("09123456789", "1234")
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs.get("timeout"), 5)

    @patch("apps.accounts.services.kavenegar_configured", return_value=True)
    @override_settings(KAVENEGAR_API_KEY="test_key", KAVENEGAR_SENDER="test_sender")
    @patch("requests.post")
    def test_send_otp_sms_timeout_error(self, mock_post, mock_configured):
        mock_post.side_effect = Exception("Connection timed out")

        with self.assertRaises(SMSDeliveryError) as ctx:
            send_otp_sms("09123456789", "1234")
        
        self.assertIn("Unexpected connection error", str(ctx.exception))


class AuthViewSetTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.url_request_otp = reverse("auth-request-otp")
        self.url_verify_otp = reverse("auth-verify-otp")

    @patch("apps.accounts.views.send_sms_otp")
    @override_settings(DEBUG=False)
    def test_request_otp_sms_delivery_error_handling(self, mock_send_sms_otp):
        from otp.dispatcher import OTPDeliveryError
        # شبیه‌سازی بروز خطا در سامانه پیامکی
        mock_send_sms_otp.side_effect = OTPDeliveryError("ارسال پیامک با خطا مواجه شد. لطفاً چند لحظه بعد دوباره تلاش کنید.")

        response = self.client.post(self.url_request_otp, {"phone": "09123456789"})

        # بررسی اینکه کد ۲۰۰ بازگردانده شده و کانال به bale تغییر یافته است
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["channel"], "bale")
        self.assertIsNotNone(cache.get("otp_09123456789"))

    @patch("apps.accounts.views.send_sms_otp", return_value="sms")
    @override_settings(DEBUG=False)
    def test_request_otp_success_with_kavenegar(self, mock_send_sms_otp):
        response = self.client.post(self.url_request_otp, {"phone": "09123456789"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "کد تأیید ارسال شد.")
        self.assertIsNone(response.data.get("otp"))
        self.assertIsNotNone(cache.get("otp_09123456789"))

    @patch("apps.accounts.views.send_sms_otp", return_value="debug")
    @override_settings(DEBUG=True)
    def test_request_otp_debug_mode_without_kavenegar(self, mock_send_sms_otp):
        response = self.client.post(self.url_request_otp, {"phone": "09123456789"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "کد تأیید ارسال شد.")
        self.assertIsNotNone(response.data.get("otp"))

    def test_verify_otp_success(self):
        cache.set("otp_09123456789", "1234", timeout=120)

        response = self.client.post(self.url_verify_otp, {
            "phone": "09123456789",
            "otp": "1234"
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["phone"], "09123456789")

    def test_verify_otp_wrong_code(self):
        cache.set("otp_09123456789", "1234", timeout=120)

        response = self.client.post(self.url_verify_otp, {
            "phone": "09123456789",
            "otp": "9999"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "کد تأیید نادرست است.")

    def test_verify_otp_expired(self):
        response = self.client.post(self.url_verify_otp, {
            "phone": "09123456789",
            "otp": "1234"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "کد تأیید منقضی شده است. لطفاً دوباره درخواست کنید.")


class OTPDispatcherTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.phone = "09123456789"
        self.otp = "5678"

    @patch("otp.dispatcher.kavenegar_configured", return_value=True)
    @patch("otp.dispatcher.send_otp_sms")
    @override_settings(DEBUG=False)
    def test_send_sms_otp_kavenegar_fallback(self, mock_send_sms, mock_configured):
        from otp.dispatcher import send_sms_otp
        
        channel = send_sms_otp(self.phone, self.otp)
        self.assertEqual(channel, "sms")
        mock_send_sms.assert_called_once_with(self.phone, self.otp)

    @patch("otp.dispatcher.kavenegar_configured", return_value=True)
    @patch("otp.dispatcher.send_otp_sms")
    @override_settings(DEBUG=False)
    def test_send_sms_otp_failure_raises_delivery_error(self, mock_send_sms, mock_configured):
        from otp.dispatcher import send_sms_otp, OTPDeliveryError
        mock_send_sms.side_effect = SMSDeliveryError("API Error")

        with self.assertRaises(OTPDeliveryError):
            send_sms_otp(self.phone, self.otp)


class RegisterPhoneChatTestCase(TestCase):
    def setUp(self):
        self.url = reverse("bot-register-phone-chat")

    @override_settings(BOT_API_KEY="supersecretkey")
    def test_register_phone_chat_success(self):
        from apps.accounts.models import User
        headers = {"X-Bot-API-Key": "supersecretkey"}
        payload = {
            "phone": "09123456789",
            "platform": "bale",
            "chat_id": "987654"
        }
        response = self.client.post(self.url, payload, headers=headers, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        user = User.objects.get(phone="09123456789")
        self.assertEqual(user.bale_chat_id, "987654")

    @override_settings(BOT_API_KEY="supersecretkey")
    def test_register_phone_chat_phone_normalization(self):
        from apps.accounts.models import User
        headers = {"X-Bot-API-Key": "supersecretkey"}
        payload = {
            "phone": "+989123456789",
            "platform": "telegram",
            "chat_id": "112233"
        }
        response = self.client.post(self.url, payload, headers=headers, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(phone="09123456789")
        self.assertEqual(user.telegram_chat_id, "112233")


class UserAdminAndResendOtpTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.url_request_otp = reverse("auth-request-otp")
        self.url_verify_otp = reverse("auth-verify-otp")

    def test_user_admin_allows_editing_and_clearing_first_and_last_name(self):
        from django.contrib import admin
        from apps.accounts.admin import CustomUserChangeForm
        from apps.accounts.models import User

        user_admin = admin.site._registry[User]
        field_names = [
            f
            for _, opts in user_admin.fieldsets
            for f in opts.get("fields", ())
        ]
        self.assertIn("first_name", field_names)
        self.assertIn("last_name", field_names)
        self.assertIn("first_name", user_admin.list_display)
        self.assertIn("last_name", user_admin.list_display)

        user = User.objects.create_user(phone="09120001122")
        user.first_name = "علی"
        user.last_name = "رضایی"
        user.save()

        form = CustomUserChangeForm(
            data={
                "phone": "09120001122",
                "first_name": "",
                "last_name": "",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
            instance=user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        saved.refresh_from_db()
        self.assertEqual(saved.first_name, "")
        self.assertEqual(saved.last_name, "")

    @patch("apps.accounts.views.send_sms_otp", return_value="sms")
    @override_settings(DEBUG=False)
    def test_request_otp_cooldown_and_delayed_previous_otp_verification(self, mock_send_sms_otp):
        res1 = self.client.post(self.url_request_otp, {"phone": "09120009988"})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        otp1 = cache.get("otp_09120009988")
        self.assertIsNotNone(otp1)
        self.assertTrue(otp1.isdigit() and 1000 <= int(otp1) <= 9999)

        # Second request within 60s returns 429 with retry_after
        res_fast = self.client.post(self.url_request_otp, {"phone": "09120009988"})
        self.assertEqual(res_fast.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("retry_after", res_fast.data)

        # Simulate cooldown expiry while otp1 is still active, then request second OTP
        cache.delete("otp_cooldown_09120009988")
        res2 = self.client.post(self.url_request_otp, {"phone": "09120009988"})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        otp2 = cache.get("otp_09120009988")
        self.assertEqual(cache.get("otp_prev_09120009988"), otp1)
        self.assertNotEqual(otp2, "")

        # Delayed first OTP still verifies smoothly!
        res_verify = self.client.post(
            self.url_verify_otp,
            {"phone": "09120009988", "otp": otp1},
        )
        self.assertEqual(res_verify.status_code, status.HTTP_200_OK)
        self.assertIn("token", res_verify.data)
        self.assertIsNone(cache.get("otp_09120009988"))
        self.assertIsNone(cache.get("otp_prev_09120009988"))
