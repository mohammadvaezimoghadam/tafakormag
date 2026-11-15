from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase, override_settings

from apps.payments.exceptions import GatewayRequestError
from apps.payments.gateways import ZarinPalGateway, get_gateway


class ZarinPalGatewayTests(SimpleTestCase):
    """Unit tests for ZarinPalGateway request/verify HTTP integration."""

    @override_settings(ZARINPAL_SANDBOX=True, ZARINPAL_MERCHANT_ID="merchant-test-uuid")
    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_sandbox_request_payment_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"code": 100, "authority": "S0000000000000000000000000000111"},
            "errors": [],
        }
        mock_post.return_value = mock_resp

        result = ZarinPalGateway().request_payment(
            amount_tomans=50000,
            description="خرید کتاب",
            callback_url="http://localhost:8000/api/v1/payments/callback/",
            mobile="09121111111",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.authority, "S0000000000000000000000000000111")
        self.assertEqual(
            result.gateway_url,
            "https://sandbox.zarinpal.com/pg/StartPay/S0000000000000000000000000000111",
        )
        called_url = mock_post.call_args.args[0]
        called_payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(called_url, "https://sandbox.zarinpal.com/pg/v4/payment/request.json")
        self.assertEqual(called_payload["currency"], "IRT")
        self.assertEqual(called_payload["amount"], 50000)

    @override_settings(ZARINPAL_SANDBOX=False, ZARINPAL_MERCHANT_ID="prod-merchant")
    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_production_verify_handles_code_100_and_101(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "code": 101,
                "ref_id": 44556677,
                "card_pan": "603799******9999",
                "fee": 500,
            },
            "errors": [],
        }
        mock_post.return_value = mock_resp

        result = ZarinPalGateway().verify_payment(
            authority="A0000000000000000000000000000999",
            amount_tomans=120000,
        )

        self.assertTrue(result.success)
        self.assertTrue(result.already_verified)
        self.assertEqual(result.ref_id, "44556677")
        self.assertEqual(result.card_pan, "603799******9999")
        self.assertEqual(result.fee, 500)
        self.assertEqual(
            mock_post.call_args.args[0],
            "https://payment.zarinpal.com/pg/v4/payment/verify.json",
        )

    @patch("apps.payments.gateways.zarinpal.requests.post", side_effect=TimeoutError("gateway timeout"))
    def test_request_payment_network_exception_returns_clean_failure(self, _mock_post):
        result = ZarinPalGateway().request_payment(
            amount_tomans=20000,
            description="تست خطا",
            callback_url="http://localhost:8000/api/v1/payments/callback/",
        )
        self.assertFalse(result.success)
        self.assertIn("gateway timeout", result.error_message)

    def test_unsupported_gateway_raises(self):
        with self.assertRaises(GatewayRequestError):
            get_gateway("unknown_bank")

