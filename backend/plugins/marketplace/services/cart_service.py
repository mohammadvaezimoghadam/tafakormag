from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.db.models import Prefetch

from ..models.cart import Cart, CartItem
from ..models.catalog import Item, ItemImage
from ..exceptions import (
    ItemNotAvailableError,
    InsufficientStockError,
    SelfPurchaseError,
    DigitalItemQuantityError,
)


class CartService:
    """
    Dedicated domain service managing shopping cart operations.
    Enforces business logic rules:
    - Sellers cannot purchase their own products.
    - Quantities cannot exceed real-time warehouse inventory.
    - Digital downloads are restricted to a maximum quantity of 1.
    - Soft-deleted or inactive catalog items are blocked from insertion.
    """

    @classmethod
    def get_or_create_cart(cls, user) -> Cart:
        """
        Retrieves the active cart for the user or creates a new one atomically.
        """
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @classmethod
    def get_cart_summary(cls, user) -> Dict[str, Any]:
        """
        Returns full cart payload including prefetched items, calculated totals,
        and logistics metadata for the checkout preview.
        """
        cart = cls.get_or_create_cart(user)

        # Optimize queries using select_related and prefetch_related
        cart_items = (
            CartItem.objects.filter(cart=cart)
            .select_related("item", "item__seller", "item__category")
            .prefetch_related(
                Prefetch(
                    "item__images",
                    queryset=ItemImage.objects.filter(is_cover=True),
                    to_attr="cover_images"
                )
            )
            .order_by("-created_at")
        )

        subtotal = Decimal("0")
        total_items_count = 0
        has_physical_items = False
        has_digital_items = False
        items_data = []

        for cart_item in cart_items:
            item = cart_item.item
            # Determine effective unit price (respects active discount prices)
            unit_price = item.discount_price if item.discount_price else item.price
            line_total = unit_price * cart_item.quantity

            subtotal += line_total
            total_items_count += cart_item.quantity

            if item.delivery_type == Item.DeliveryType.PHYSICAL:
                has_physical_items = True
            elif item.delivery_type == Item.DeliveryType.DIGITAL:
                has_digital_items = True

            cover_image_url = None
            if hasattr(item, "cover_images") and item.cover_images:
                cover_image_url = item.cover_images[0].image_url if item.cover_images[0].image_url else None
            elif item.images.exists():
                cover_image_url = item.images.first().image_url

            items_data.append({
                "cart_item_id": cart_item.id,
                "item_id": item.id,
                "title": item.title,
                "slug": item.slug,
                "seller_name": item.seller.get_full_name() or item.seller.phone,
                "deal_type": item.deal_type,
                "delivery_type": item.delivery_type,
                "unit_price": unit_price,
                "original_price": item.price,
                "quantity": cart_item.quantity,
                "stock": item.stock,
                "is_unlimited_stock": item.is_unlimited_stock,
                "line_total": line_total,
                "cover_image": cover_image_url,
                "is_available": (item.status == Item.Status.AVAILABLE),
            })

        return {
            "cart_id": cart.id,
            "total_items_count": total_items_count,
            "subtotal": subtotal,
            "has_physical_items": has_physical_items,
            "has_digital_items": has_digital_items,
            "items": items_data,
        }

    @classmethod
    @transaction.atomic
    def add_item(cls, user, item_id: int, quantity: int = 1) -> CartItem:
        """
        Adds an item to user's cart or increments quantity if already present.
        Enforces inventory availability, digital limits, and self-purchase rules.
        """
        if quantity <= 0:
            quantity = 1

        try:
            item = Item.objects.select_for_update().get(id=item_id)
        except Item.DoesNotExist:
            raise ItemNotAvailableError("کالای مورد نظر یافت نشد.")

        # Business Rule 1: Item must be available
        if item.status != Item.Status.AVAILABLE:
            raise ItemNotAvailableError("این کالا در حال حاضر قابل خرید نیست.")

        # Business Rule 2: Cannot purchase own item
        if item.seller_id == user.id:
            raise SelfPurchaseError("شما نمی‌توانید کالای ثبت‌شده توسط خودتان را به سبد خرید اضافه کنید.")

        # Business Rule 3: Digital files are capped at quantity 1
        if item.delivery_type == Item.DeliveryType.DIGITAL and quantity > 1:
            raise DigitalItemQuantityError("برای فایل‌های دانلودی فقط امکان ثبت ۱ نسخه وجود دارد.")

        cart = cls.get_or_create_cart(user)
        cart_item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart,
            item=item,
            defaults={"quantity": quantity}
        )

        if not created:
            # Item already exists in cart, compute requested total quantity
            new_quantity = cart_item.quantity + quantity

            # Check digital item limit
            if item.delivery_type == Item.DeliveryType.DIGITAL and new_quantity > 1:
                raise DigitalItemQuantityError("این فایل دیجیتال قبلاً در سبد خرید شما ثبت شده است.")

            # Business Rule 4: Real-time stock validation
            if not item.is_unlimited_stock and new_quantity > item.stock:
                raise InsufficientStockError(
                    f"موجودی این کالا ({item.stock} عدد) برای تعداد درخواستی شما کافی نیست."
                )

            cart_item.quantity = new_quantity
            cart_item.save(update_fields=["quantity", "updated_at"])
        else:
            # Newly inserted cart item, check stock
            if not item.is_unlimited_stock and quantity > item.stock:
                raise InsufficientStockError(
                    f"موجودی این کالا ({item.stock} عدد) کمتر از تعداد درخواستی است."
                )

        return cart_item

    @classmethod
    @transaction.atomic
    def update_quantity(cls, user, cart_item_id: int, quantity: int) -> Optional[CartItem]:
        """
        Updates the quantity of a specific cart item.
        If quantity is set to 0 or less, removes the item from the cart.
        """
        cart = cls.get_or_create_cart(user)

        try:
            cart_item = CartItem.objects.select_related("item").select_for_update().get(
                id=cart_item_id,
                cart=cart
            )
        except CartItem.DoesNotExist:
            raise ItemNotAvailableError("آیتم مورد نظر در سبد خرید شما یافت نشد.")

        # If zero or negative, delete item
        if quantity <= 0:
            cart_item.delete()
            return None

        item = cart_item.item

        # Digital items restriction
        if item.delivery_type == Item.DeliveryType.DIGITAL and quantity > 1:
            raise DigitalItemQuantityError("برای فایل‌های دانلودی امکان انتخاب بیش از ۱ نسخه وجود ندارد.")

        # Check warehouse stock
        if not item.is_unlimited_stock and quantity > item.stock:
            raise InsufficientStockError(
                f"حداکثر موجودی قابل سفارش برای این کالا {item.stock} عدد است."
            )

        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity", "updated_at"])
        return cart_item

    @classmethod
    def remove_item(cls, user, cart_item_id: int) -> bool:
        """
        Safely removes an item from the user's cart.
        """
        cart = cls.get_or_create_cart(user)
        deleted_count, _ = CartItem.objects.filter(id=cart_item_id, cart=cart).delete()
        return deleted_count > 0

    @classmethod
    def clear_cart(cls, user) -> int:
        """
        Empties all items from the user's cart (typically after order creation).
        """
        cart = cls.get_or_create_cart(user)
        deleted_count, _ = CartItem.objects.filter(cart=cart).delete()
        return deleted_count
