from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase

from apps.donations.models import DonationCampaign
from apps.marketplace.models.catalog import Category, Item
from apps.marketplace.models.location import Address, City, Province
from apps.marketplace.models.order import Order
from apps.marketplace.models.payment import Payment, SellerSettlement
from apps.marketplace.services.cart_service import CartService
from apps.marketplace.services.order_service import OrderService
from apps.notes.models import Topic
from apps.payments.models import PaymentTransaction

User = get_user_model()


class UnifiedPaymentsAPITests(APITestCase):
    """End-to-end API tests across payments, donations, and marketplace integration."""

    def setUp(self):
        self.buyer = User.objects.create_user(phone="09121112233", password="password123")
        self.seller = User.objects.create_user(phone="09124445566", password="password123")
        self.topic = Topic.objects.create(name="تاپیک نیکوکاری", created_by=self.seller)
        self.campaign = DonationCampaign.objects.create(
            topic=self.topic,
            creator=self.seller,
            title="پویش کتاب و لوازم‌التحریر",
            description="کمک به دانش‌آموزان",
            target_amount=5000000,
        )

        category = Category.objects.create(name="کتاب", slug="books")
        province = Province.objects.create(name="تهران")
        city = City.objects.create(province=province, name="تهران")
        self.address = Address.objects.create(
            user=self.buyer,
            title="خانه",
            receiver_name="خریدار نمونه",
            receiver_phone="09121112233",
            city=city,
            postal_address="تهران، خیابان انقلاب، پلاک ۵",
            postal_code="1111111111",
            is_default=True,
        )
        self.paid_book = Item.objects.create(
            seller=self.seller,
            category=category,
            title="کتاب اندیشه",
            slug="andisheh-book",
            delivery_type=Item.DeliveryType.PHYSICAL,
            price=Decimal("120000"),
            stock=3,
            status=Item.Status.AVAILABLE,
        )
        self.free_book = Item.objects.create(
            seller=self.seller,
            category=category,
            title="کتابچه رایگان",
            slug="free-booklet",
            delivery_type=Item.DeliveryType.DIGITAL,
            price=Decimal("0"),
            stock=1,
            is_unlimited_stock=True,
            status=Item.Status.AVAILABLE,
        )

    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_marketplace_initiate_and_central_callback_with_deeplink(self, mock_post):
        init_resp = MagicMock()
        init_resp.json.return_value = {
            "data": {"code": 100, "authority": "S000000000000000000000000000MKT001"},
            "errors": [],
        }
        verify_resp = MagicMock()
        verify_resp.json.return_value = {
            "data": {"code": 100, "ref_id": 55443322, "card_pan": "603799******4321", "fee": 0},
            "errors": [],
        }
        mock_post.side_effect = [init_resp, verify_resp]

        CartService.add_item(user=self.buyer, item_id=self.paid_book.id, quantity=1)
        order = OrderService.create_order_from_cart(user=self.buyer, shipping_address_id=self.address.id)

        self.client.force_authenticate(user=self.buyer)
        init_res = self.client.post(
            "/api/v1/marketplace/payments/initiate/",
            {
                "order_id": order.id,
                "client_redirect_url": "tafakorshop://payment-result",
            },
            format="json",
        )
        self.assertEqual(init_res.status_code, status.HTTP_200_OK)
        self.assertFalse(init_res.data["is_free"])
        self.assertEqual(init_res.data["authority"], "S000000000000000000000000000MKT001")
        self.assertIn("StartPay/S000000000000000000000000000MKT001", init_res.data["payment_url"])

        # Bank redirects browser to centralized /api/v1/payments/callback/
        cb_res = self.client.get(
            "/api/v1/payments/callback/?Authority=S000000000000000000000000000MKT001&Status=OK"
        )
        self.assertEqual(cb_res.status_code, status.HTTP_302_FOUND)
        self.assertTrue(cb_res["Location"].startswith("tafakorshop://payment-result?"))
        self.assertIn("payment=success", cb_res["Location"])
        self.assertIn("ref_id=55443322", cb_res["Location"])

        # Order, Marketplace Payment, Inventory, and Escrow must all be fulfilled
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)

        self.paid_book.refresh_from_db()
        self.assertEqual(self.paid_book.stock, 2)

        mkt_payment = Payment.objects.get(order=order)
        self.assertEqual(mkt_payment.status, Payment.Status.SUCCESSFUL)
        self.assertEqual(mkt_payment.tracking_code, "55443322")
        self.assertIsNotNone(mkt_payment.payment_transaction_id)
        self.assertTrue(SellerSettlement.objects.filter(shipment__order=order).exists())

    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_marketplace_verify_endpoint_and_free_order_flow(self, mock_post):
        # 1. Free digital order settles immediately without bank call
        CartService.add_item(user=self.buyer, item_id=self.free_book.id, quantity=1)
        free_order = OrderService.create_order_from_cart(user=self.buyer)

        self.client.force_authenticate(user=self.buyer)
        free_res = self.client.post(
            "/api/v1/marketplace/payments/initiate/",
            {"order_id": free_order.id},
            format="json",
        )
        self.assertEqual(free_res.status_code, status.HTTP_200_OK)
        self.assertTrue(free_res.data["is_free"])
        free_order.refresh_from_db()
        self.assertEqual(free_order.payment_status, Order.PaymentStatus.PAID)
        mock_post.assert_not_called()

        # 2. Paid order verified via /api/v1/marketplace/payments/verify/
        init_resp = MagicMock()
        init_resp.json.return_value = {
            "data": {"code": 100, "authority": "S000000000000000000000000000MKT002"},
            "errors": [],
        }
        verify_resp = MagicMock()
        verify_resp.json.return_value = {
            "data": {"code": 100, "ref_id": 66778899},
            "errors": [],
        }
        mock_post.side_effect = [init_resp, verify_resp]

        CartService.add_item(user=self.buyer, item_id=self.paid_book.id, quantity=1)
        paid_order = OrderService.create_order_from_cart(user=self.buyer, shipping_address_id=self.address.id)

        self.client.post(
            "/api/v1/marketplace/payments/initiate/",
            {"order_id": paid_order.id},
            format="json",
        )
        verify_res = self.client.post(
            "/api/v1/marketplace/payments/verify/",
            {"authority": "S000000000000000000000000000MKT002", "status": "OK"},
            format="json",
        )
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_res.data["success"])
        self.assertEqual(verify_res.data["ref_id"], "66778899")
        paid_order.refresh_from_db()
        self.assertEqual(paid_order.payment_status, Order.PaymentStatus.PAID)

    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_central_callback_blocks_untrusted_redirect_and_renders_html_receipt(self, mock_post):
        init_resp = MagicMock()
        init_resp.json.return_value = {
            "data": {"code": 100, "authority": "S000000000000000000000000000OPENRED"},
            "errors": [],
        }
        verify_resp = MagicMock()
        verify_resp.json.return_value = {
            "data": {"code": 100, "ref_id": 33445566},
            "errors": [],
        }
        mock_post.side_effect = [init_resp, verify_resp]

        CartService.add_item(user=self.buyer, item_id=self.paid_book.id, quantity=1)
        order = OrderService.create_order_from_cart(user=self.buyer, shipping_address_id=self.address.id)

        self.client.force_authenticate(user=self.buyer)
        self.client.post(
            "/api/v1/marketplace/payments/initiate/",
            {
                "order_id": order.id,
                "client_redirect_url": "https://evil-attacker.example/steal",
            },
            format="json",
        )

        # Should NOT redirect to untrusted domain; renders safe HTML receipt instead
        with override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"]):
            cb_res = self.client.get(
                "/api/v1/payments/callback/?Authority=S000000000000000000000000000OPENRED&Status=OK"
            )
        self.assertEqual(cb_res.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", cb_res["Content-Type"])
        self.assertIn("33445566", cb_res.content.decode("utf-8"))

    @patch("apps.payments.gateways.zarinpal.requests.post")
    def test_donation_through_central_callback_and_history_no_n_plus_1(self, mock_post):
        mock_init = MagicMock()
        mock_init.json.return_value = {
            "data": {"code": 100, "authority": "S000000000000000000000000000DON001"},
            "errors": [],
        }
        mock_verify = MagicMock()
        mock_verify.json.return_value = {
            "data": {"code": 100, "ref_id": 99887766},
            "errors": [],
        }
        mock_post.side_effect = [mock_init, mock_verify]

        self.client.force_authenticate(user=self.buyer)
        donate_res = self.client.post(
            f"/api/v1/donations/campaigns/{self.campaign.id}/donate/",
            {"amount": 75000, "is_anonymous": False},
            format="json",
        )
        self.assertEqual(donate_res.status_code, status.HTTP_201_CREATED)

        # Create additional history records for the buyer (plus one for seller that must not leak)
        for idx in range(5):
            PaymentTransaction.objects.create(
                user=self.buyer,
                purpose=PaymentTransaction.Purpose.OTHER,
                reference_id=f"EXTRA-{idx}",
                amount=10000 + idx,
                authority=f"AUTH_EXTRA_{idx}",
            )
        PaymentTransaction.objects.create(
            user=self.seller,
            purpose=PaymentTransaction.Purpose.OTHER,
            reference_id="SELLER-PRIV",
            amount=99000,
            authority="AUTH_SELLER_PRIV",
        )

        # Central callback works cleanly for donation and redirects to /donate
        cb_res = self.client.get(
            "/api/v1/payments/callback/?Authority=S000000000000000000000000000DON001&Status=OK"
        )
        self.assertEqual(cb_res.status_code, status.HTTP_302_FOUND)
        self.assertIn("/donate?", cb_res["Location"])
        self.assertIn("payment=success", cb_res["Location"])

        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.collected_amount, 75000)

        # Transactions list must only return buyer's 6 records with minimal constant queries
        with CaptureQueriesContext(connection) as ctx:
            list_res = self.client.get("/api/v1/payments/transactions/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 6)
        self.assertLessEqual(len(ctx), 3)

