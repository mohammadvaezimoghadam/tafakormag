from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from apps.payments.exceptions import GatewayVerificationError, PaymentNotFoundError
from apps.payments.handlers import register_payment_handler
from apps.payments.models import PaymentTransaction
from apps.payments.services import PaymentService

User = get_user_model()


class PaymentServiceTests(TransactionTestCase):
    """Service-layer tests for orchestration, idempotency, and bank-proof durability."""

    def setUp(self):
        self.user = User.objects.create_user(phone="09120000001")
        self.calls: list[str] = []

        def sample_handler(payment_trx: PaymentTransaction):
            self.calls.append(str(payment_trx.id))

        register_payment_handler(PaymentTransaction.Purpose.OTHER, sample_handler)

    def tearDown(self):
        from apps.payments.handlers import _DOMAIN_REGISTRY

        _DOMAIN_REGISTRY.pop(PaymentTransaction.Purpose.OTHER, None)
        super().tearDown()

    def test_zero_amount_settles_without_gateway(self):
        trx, gateway_url = PaymentService.initiate_payment(
            purpose=PaymentTransaction.Purpose.OTHER,
            reference_id="FREE-REF-1",
            amount_tomans=0,
            user=self.user,
            description="تراکنش رایگان",
        )

        self.assertIsNone(gateway_url)
        self.assertEqual(trx.gateway, PaymentTransaction.Gateway.FREE)
        self.assertEqual(trx.status, PaymentTransaction.Status.SUCCESSFUL)
        self.assertIsNotNone(trx.settled_at)
        self.assertEqual(self.calls, [str(trx.id)])

    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_verify_is_idempotent_and_calls_handler_once(self, mock_post):
        init_resp = MagicMock()
        init_resp.json.return_value = {
            "data": {"code": 100, "authority": "S000000000000000000000000000IDEMP01"},
            "errors": [],
        }
        verify_resp = MagicMock()
        verify_resp.json.return_value = {
            "data": {"code": 100, "ref_id": 77889900, "card_pan": "502229******0001", "fee": 0},
            "errors": [],
        }
        mock_post.side_effect = [init_resp, verify_resp]

        trx, _ = PaymentService.initiate_payment(
            purpose=PaymentTransaction.Purpose.OTHER,
            reference_id="REF-IDEMP",
            amount_tomans=85000,
            user=self.user,
        )

        settled_1, already_1 = PaymentService.verify_and_finalize(authority=trx.authority)
        settled_2, already_2 = PaymentService.verify_and_finalize(authority=trx.authority)

        self.assertFalse(already_1)
        self.assertTrue(already_2)
        self.assertEqual(settled_1.status, PaymentTransaction.Status.SUCCESSFUL)
        self.assertEqual(settled_2.ref_id, "77889900")
        self.assertEqual(len(self.calls), 1)
        # Only 2 HTTP calls total: request + single verify (no duplicate verify on 2nd call)
        self.assertEqual(mock_post.call_count, 2)

    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_bank_proof_survives_domain_handler_failure_and_recovers(self, mock_post):
        init_resp = MagicMock()
        init_resp.json.return_value = {
            "data": {"code": 100, "authority": "S000000000000000000000000000RECOVER1"},
            "errors": [],
        }
        verify_resp = MagicMock()
        verify_resp.json.return_value = {
            "data": {"code": 100, "ref_id": 11223344, "card_pan": "621986******2222", "fee": 100},
            "errors": [],
        }
        mock_post.side_effect = [init_resp, verify_resp]

        attempts = {"count": 0}

        def flaky_handler(payment_trx: PaymentTransaction):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("Transient domain lock timeout")

        register_payment_handler(PaymentTransaction.Purpose.OTHER, flaky_handler)

        trx, _ = PaymentService.initiate_payment(
            purpose=PaymentTransaction.Purpose.OTHER,
            reference_id="REF-RECOVER",
            amount_tomans=45000,
            user=self.user,
        )

        with self.assertRaises(RuntimeError):
            PaymentService.verify_and_finalize(authority=trx.authority)

        # Bank proof must survive the rolled-back domain block!
        trx.refresh_from_db()
        self.assertEqual(trx.status, PaymentTransaction.Status.VERIFIED)
        self.assertEqual(trx.ref_id, "11223344")
        self.assertIn("Transient domain lock timeout", trx.failure_reason)

        # Retrying does NOT hit bank again; finishes domain settlement cleanly
        recovered_trx, already = PaymentService.verify_and_finalize(authority=trx.authority)
        self.assertFalse(already)
        self.assertEqual(recovered_trx.status, PaymentTransaction.Status.SUCCESSFUL)
        self.assertEqual(mock_post.call_count, 2)

    def test_verify_missing_authority_raises_not_found(self):
        with self.assertRaises(PaymentNotFoundError):
            PaymentService.verify_and_finalize(authority="NON_EXISTENT_AUTH")

    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_cancel_marks_cancelled_without_bank_verify(self, mock_post):
        init_resp = MagicMock()
        init_resp.json.return_value = {
            "data": {"code": 100, "authority": "S000000000000000000000000000CANCEL1"},
            "errors": [],
        }
        mock_post.return_value = init_resp

        trx, _ = PaymentService.initiate_payment(
            purpose=PaymentTransaction.Purpose.OTHER,
            reference_id="REF-CANCEL",
            amount_tomans=30000,
            user=self.user,
        )

        with self.assertRaises(GatewayVerificationError):
            PaymentService.verify_and_finalize(authority=trx.authority, status_param="NOK")

        trx.refresh_from_db()
        self.assertEqual(trx.status, PaymentTransaction.Status.CANCELLED)
        self.assertEqual(mock_post.call_count, 1)
