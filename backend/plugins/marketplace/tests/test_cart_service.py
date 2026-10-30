from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models.catalog import Category, Item
from ..models.cart import Cart, CartItem
from ..services.cart_service import CartService
from ..exceptions import (
    SelfPurchaseError,
    InsufficientStockError,
    DigitalItemQuantityError,
    ItemNotAvailableError,
)

User = get_user_model()


class CartServiceTests(TestCase):
    """
    Automated integration tests verifying shopping cart business logic.
    """

    def setUp(self):
        # Create test users
        self.seller = User.objects.create_user(phone="09121111111", password="password123")
        self.buyer = User.objects.create_user(phone="09122222222", password="password123")

        # Create category
        self.category = Category.objects.create(name="کتب درسی", slug="textbooks")

        # Create physical book
        self.physical_book = Item.objects.create(
            seller=self.seller,
            category=self.category,
            title="کتاب ریاضی عمومی ۱",
            slug="math-1",
            deal_type=Item.DealType.SALE,
            delivery_type=Item.DeliveryType.PHYSICAL,
            price=Decimal("150000"),
            discount_price=Decimal("120000"),
            stock=5,
            status=Item.Status.AVAILABLE,
        )

        # Create digital book
        self.digital_book = Item.objects.create(
            seller=self.seller,
            category=self.category,
            title="کتاب الکترونیکی فیزیک",
            slug="physics-pdf",
            deal_type=Item.DealType.SALE,
            delivery_type=Item.DeliveryType.DIGITAL,
            price=Decimal("80000"),
            stock=1,
            is_unlimited_stock=True,
            status=Item.Status.AVAILABLE,
        )

    def test_add_item_success(self):
        """Buyer successfully adds an available item to cart."""
        cart_item = CartService.add_item(user=self.buyer, item_id=self.physical_book.id, quantity=2)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.item, self.physical_book)

    def test_cannot_purchase_own_item(self):
        """Seller cannot add their own item to cart (anti-fraud)."""
        with self.assertRaises(SelfPurchaseError):
            CartService.add_item(user=self.seller, item_id=self.physical_book.id, quantity=1)

    def test_cannot_exceed_warehouse_stock(self):
        """Attempting to add more items than available warehouse stock raises error."""
        with self.assertRaises(InsufficientStockError):
            CartService.add_item(user=self.buyer, item_id=self.physical_book.id, quantity=10)

    def test_digital_item_max_quantity_one(self):
        """Digital download files are restricted to a maximum quantity of 1."""
        with self.assertRaises(DigitalItemQuantityError):
            CartService.add_item(user=self.buyer, item_id=self.digital_book.id, quantity=2)

    def test_update_quantity_to_zero_removes_item(self):
        """Updating quantity to 0 removes the item from the cart safely."""
        cart_item = CartService.add_item(user=self.buyer, item_id=self.physical_book.id, quantity=2)
        updated = CartService.update_quantity(user=self.buyer, cart_item_id=cart_item.id, quantity=0)
        self.assertIsNone(updated)
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())

    def test_cart_summary_calculation(self):
        """Cart summary properly calculates subtotal with effective discount price."""
        CartService.add_item(user=self.buyer, item_id=self.physical_book.id, quantity=2)
        CartService.add_item(user=self.buyer, item_id=self.digital_book.id, quantity=1)

        summary = CartService.get_cart_summary(self.buyer)
        self.assertEqual(summary["total_items_count"], 3)
        self.assertTrue(summary["has_physical_items"])
        self.assertTrue(summary["has_digital_items"])

        # Expected: 2 * 120,000 (discount price) + 1 * 80,000 = 320,000 Toman
        expected_subtotal = (Decimal("120000") * 2) + Decimal("80000")
        self.assertEqual(summary["subtotal"], expected_subtotal)
