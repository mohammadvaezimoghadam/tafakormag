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
        mock_response.content = b"success"
        mock_post.return_value = mock_response

        # نباید هیچ خطایی پرتاب شود
        send_otp_sms("09123456789", "1234")
        mock_post.assert_called_once()
        # بررسی اینکه در آرگومان‌های فراخوانی requests.post حتماً timeout وجود داشته است
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs.get("timeout"), 5)

    @patch("apps.accounts.services.kavenegar_configured", return_value=True)
    @override_settings(KAVENEGAR_API_KEY="test_key", KAVENEGAR_SENDER="test_sender")
    @patch("requests.post")
    def test_send_otp_sms_timeout_error(self, mock_post, mock_configured):
        # شبیه‌سازی رخ دادن خطا/تایم‌اوت در requests.post
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaises(SMSDeliveryError) as ctx:
            send_otp_sms("09123456789", "1234")
        
        self.assertIn("Unexpected connection error", str(ctx.exception))


class AuthViewSetTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.url_request_otp = reverse("user-request-otp")
        self.url_verify_otp = reverse("user-verify-otp")

    @patch("apps.accounts.views.kavenegar_configured", return_value=True)
    @override_settings(DEBUG=False)
    @patch("apps.accounts.views.send_otp_sms")
    def test_request_otp_sms_delivery_error_handling(self, mock_send_sms, mock_configured):
        # شبیه‌سازی بروز خطا در سامانه پیامکی
        mock_send_sms.side_effect = SMSDeliveryError("API Error")

        response = self.client.post(self.url_request_otp, {"phone": "09123456789"})

        # بررسی اینکه کد ۵۰۳ بازگردانده شده است
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            response.data["error"],
            "ارسال پیامک با خطا مواجه شد. لطفاً چند لحظه بعد دوباره تلاش کنید."
        )

        # بررسی اینکه کش مربوط به این شماره تلفن پاک شده است تا درخواست در آینده مسدود نباشد
        self.assertIsNone(cache.get("otp_09123456789"))

    @patch("apps.accounts.views.kavenegar_configured", return_value=True)
    @override_settings(DEBUG=False)
    @patch("apps.accounts.views.send_otp_sms")
    def test_request_otp_success_with_kavenegar(self, mock_send_sms, mock_configured):
        response = self.client.post(self.url_request_otp, {"phone": "09123456789"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "کد تأیید ارسال شد.")
        # در حالت غیر DEBUG نباید کد OTP در ریسپانس فرستاده شود
        self.assertIsNone(response.data.get("otp"))

        # بررسی وجود کد در کش
        self.assertIsNotNone(cache.get("otp_09123456789"))

    @patch("apps.accounts.views.kavenegar_configured", return_value=False)
    @override_settings(DEBUG=True)
    def test_request_otp_debug_mode_without_kavenegar(self, mock_configured):
        response = self.client.post(self.url_request_otp, {"phone": "09123456789"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "کد تأیید ارسال شد.")
        # در حالت DEBUG و بدون کاوه‌نگار باید کد OTP در ریسپانس فرستاده شود
        self.assertIsNotNone(response.data.get("otp"))

    def test_verify_otp_success(self):
        # قرار دادن کد فرضی در کش
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
        # کدی در کش ذخیره نشده است (منقضی شده)
        response = self.client.post(self.url_verify_otp, {
            "phone": "09123456789",
            "otp": "1234"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "کد تأیید منقضی شده است. لطفاً دوباره درخواست کنید.")
