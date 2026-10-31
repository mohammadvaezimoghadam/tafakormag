from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models.catalog import Category, Item
from ..models.location import Province, City, Address
from ..models.order import Order, OrderShipment
from ..models.interaction import DigitalAccess
from ..models.payment import SellerSettlement
from ..services.cart_service import CartService
from ..services.order_service import OrderService

User = get_user_model()


class OrderServiceTests(TestCase):
    """
    Automated tests verifying multi-vendor order checkout, stock reservation,
    and payment fulfillment.
    """

    def setUp(self):
        self.buyer = User.objects.create_user(phone="09121111111", password="password123")
        self.seller_1 = User.objects.create_user(phone="09122222222", password="password123")
        self.seller_2 = User.objects.create_user(phone="09123333333", password="password123")

        self.category = Category.objects.create(name="ادبیات", slug="literature")

        # Location setup
        self.province = Province.objects.create(name="تهران")
        self.city = City.objects.create(province=self.province, name="تهران")
        self.address = Address.objects.create(
            user=self.buyer,
            title="منزل",
            receiver_name="علی خریدار",
            receiver_phone="09121111111",
            city=self.city,
            postal_address="خیابان آزادی، کوچه مریم، پلاک ۱۰",
            postal_code="1234567890",
            is_default=True,
        )

        # Book from Seller 1 (Physical)
        self.book_1 = Item.objects.create(
            seller=self.seller_1,
            category=self.category,
            title="کتاب فیزیکی فروشنده ۱",
            slug="book-1",
            delivery_type=Item.DeliveryType.PHYSICAL,
            price=Decimal("100000"),
            stock=5,
            status=Item.Status.AVAILABLE,
        )

        # Book from Seller 2 (Digital PDF)
        self.book_2 = Item.objects.create(
            seller=self.seller_2,
            category=self.category,
            title="کتاب دانلودی فروشنده ۲",
            slug="book-2",
            delivery_type=Item.DeliveryType.DIGITAL,
            price=Decimal("50000"),
            stock=1,
            is_unlimited_stock=True,
            status=Item.Status.AVAILABLE,
        )

    def test_multi_vendor_checkout_and_reservation(self):
        """Checkout splits multi-vendor items into separate shipments and reserves stock."""
        CartService.add_item(user=self.buyer, item_id=self.book_1.id, quantity=1)
        CartService.add_item(user=self.buyer, item_id=self.book_2.id, quantity=1)

        order = OrderService.create_order_from_cart(
            user=self.buyer,
            shipping_address_id=self.address.id,
        )

        # 1. Verify parent order
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertEqual(order.total_items_amount, Decimal("150000"))
        self.assertEqual(order.payable_amount, Decimal("150000"))

        # 2. Verify Multi-Vendor Split: exactly 2 distinct shipments
        self.assertEqual(order.shipments.count(), 2)
        sellers_in_shipments = set(order.shipments.values_list("seller_id", flat=True))
        self.assertEqual(sellers_in_shipments, {self.seller_1.id, self.seller_2.id})

        # 3. Verify stock reservation is active
        self.book_1.refresh_from_db()
        self.assertIsNotNone(self.book_1.reserved_until)

        # 4. Verify cart was cleared
        summary = CartService.get_cart_summary(self.buyer)
        self.assertEqual(summary["total_items_count"], 0)

    def test_confirm_payment_fulfills_order_and_escrow(self):
        """Payment confirmation deducts inventory, creates digital access, and holds escrow."""
        CartService.add_item(user=self.buyer, item_id=self.book_1.id, quantity=1)
        CartService.add_item(user=self.buyer, item_id=self.book_2.id, quantity=1)

        order = OrderService.create_order_from_cart(
            user=self.buyer,
            shipping_address_id=self.address.id,
        )

        # Confirm payment
        OrderService.confirm_payment_success(order=order, payment_reference="REF-TEST-9988")

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)

        # Physical book stock decremented from 5 to 4
        self.book_1.refresh_from_db()
        self.assertEqual(self.book_1.stock, 4)
        self.assertIsNone(self.book_1.reserved_until)

        # Digital access granted to buyer
        digital_access = DigitalAccess.objects.filter(user=self.buyer, item=self.book_2).first()
        self.assertIsNotNone(digital_access)
        self.assertEqual(digital_access.granted_via, DigitalAccess.GrantedVia.PURCHASE)

        # Escrow settlements created for both vendors in status HELD
        settlements = SellerSettlement.objects.filter(shipment__order=order)
        self.assertEqual(settlements.count(), 2)
        for s in settlements:
            self.assertEqual(s.status, SellerSettlement.Status.HELD)
            self.assertGreater(s.gross_amount, 0)
            self.assertGreater(s.net_amount, 0)
