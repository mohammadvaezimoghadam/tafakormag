from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models.discount import Coupon, CouponUsage
from ..models.order import Order
from ..models.catalog import Category, Item
from ..models.cart import CartItem
from ..services.cart_service import CartService
from ..services.coupon_service import CouponService
from ..exceptions import InvalidCouponError

User = get_user_model()


class CouponServiceTests(TestCase):
    """
    Automated tests verifying discount coupons, caps, and fraud prevention.
    """

    def setUp(self):
        self.user = User.objects.create_user(phone="09123333333", password="password123")
        self.seller = User.objects.create_user(phone="09124444444", password="password123")
        self.category = Category.objects.create(name="عمومی", slug="general")

        self.item = Item.objects.create(
            seller=self.seller,
            category=self.category,
            title="کتاب آزمایشی",
            slug="test-book",
            price=Decimal("200000"),
            stock=10,
            status=Item.Status.AVAILABLE,
        )

        cart_item = CartService.add_item(user=self.user, item_id=self.item.id, quantity=1)
        self.cart_items = [cart_item]

    def test_percentage_coupon_with_cap(self):
        """20% discount on 200,000 is 40,000, capped at 30,000."""
        coupon = Coupon.objects.create(
            code="SALE20",
            discount_type=Coupon.DiscountType.PERCENTAGE,
            discount_value=Decimal("20"),
            max_discount_amount=Decimal("30000"),
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=7),
            is_active=True,
        )

        res = CouponService.validate_and_calculate_discount(
            code="sale20",  # Case-insensitive
            user=self.user,
            cart_items=self.cart_items,
            total_items_amount=Decimal("200000"),
        )
        self.assertEqual(res["discount_amount"], Decimal("30000"))

    def test_coupon_user_usage_limit(self):
        """A user cannot exceed their individual per-user usage limit."""
        coupon = Coupon.objects.create(
            code="ONCEONLY",
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("50000"),
            user_usage_limit=1,
            valid_from=timezone.now() - timedelta(days=1),
            is_active=True,
        )

        # First usage works
        res = CouponService.validate_and_calculate_discount(
            code="ONCEONLY",
            user=self.user,
            cart_items=self.cart_items,
            total_items_amount=Decimal("200000"),
        )
        self.assertEqual(res["discount_amount"], Decimal("50000"))

        # Simulate recording this usage with an order
        mock_order = Order.objects.create(
            buyer=self.user,
            order_number="ORD-TEST-USAGE",
            total_items_amount=Decimal("200000"),
            total_shipping_cost=Decimal("0"),
            payable_amount=Decimal("150000"),
        )
        CouponUsage.objects.create(
            coupon=coupon,
            user=self.user,
            order=mock_order,
            discount_applied=Decimal("50000")
        )

        # Second usage should fail
        with self.assertRaises(InvalidCouponError):
            CouponService.validate_and_calculate_discount(
                code="ONCEONLY",
                user=self.user,
                cart_items=self.cart_items,
                total_items_amount=Decimal("200000"),
            )

    def test_expired_coupon_rejected(self):
        """Expired coupons cannot be redeemed."""
        Coupon.objects.create(
            code="OLDCOUPON",
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("10000"),
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1),
            is_active=True,
        )

        with self.assertRaises(InvalidCouponError):
            CouponService.validate_and_calculate_discount(
                code="OLDCOUPON",
                user=self.user,
                cart_items=self.cart_items,
                total_items_amount=Decimal("200000"),
            )

    def test_min_order_amount_threshold(self):
        """Coupons requiring higher minimum spend fail on smaller carts."""
        Coupon.objects.create(
            code="BIGSPEND",
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("50000"),
            min_order_amount=Decimal("500000"),  # Requires 500,000 Toman
            valid_from=timezone.now() - timedelta(days=1),
            is_active=True,
        )

        with self.assertRaises(InvalidCouponError):
            CouponService.validate_and_calculate_discount(
                code="BIGSPEND",
                user=self.user,
                cart_items=self.cart_items,
                total_items_amount=Decimal("200000"),  # Only 200,000 in cart
            )
