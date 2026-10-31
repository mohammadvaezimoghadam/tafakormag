import uuid
from decimal import Decimal
from datetime import timedelta
from typing import Dict, Any, Optional
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings

from ..models.order import Order, OrderShipment, OrderItem, OrderStatusHistory, ShipmentStatusHistory
from ..models.cart import Cart, CartItem
from ..models.catalog import Item
from ..models.location import Address
from ..models.discount import Coupon, CouponUsage
from ..models.interaction import DigitalAccess
from ..models.payment import SellerSettlement
from ..services.cart_service import CartService
from ..services.coupon_service import CouponService
from ..exceptions import (
    CartEmptyError,
    ItemNotAvailableError,
    InsufficientStockError,
    ShippingAddressRequiredError,
    InvalidAddressError,
    InvalidCouponError,
    OrderCheckoutError,
)


class OrderService:
    """
    Core domain service managing checkout, multi-vendor order orchestration,
    escrow settlements, and inventory reservation.
    """
    # Reservation lock duration while customer is at the payment gateway
    RESERVATION_MINUTES = 20
    # Platform default commission percentage (e.g., 5%)
    PLATFORM_COMMISSION_PERCENT = Decimal("0.05")

    @classmethod
    def generate_order_number(cls) -> str:
        """
        Generates a human-friendly, collision-resistant unique order number.
        Example: ORD-20261027-A8F29C
        """
        date_str = timezone.now().strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"ORD-{date_str}-{random_suffix}"

    @classmethod
    @transaction.atomic
    def create_order_from_cart(
        cls,
        user,
        shipping_address_id: Optional[int] = None,
        coupon_code: Optional[str] = None
    ) -> Order:
        """
        Atomically converts the user's active shopping cart into a multi-vendor Order.
        - Validates real-time inventory and status.
        - Validates shipping address if physical goods are included.
        - Groups items by seller and generates individual OrderShipment packages.
        - Applies temporary stock reservation (anti-race condition).
        - Clears the user's cart upon success.
        """
        cart = CartService.get_or_create_cart(user)
        cart_items = list(
            CartItem.objects.filter(cart=cart)
            .select_related("item", "item__seller")
            .select_for_update()
        )

        if not cart_items:
            raise CartEmptyError("سبد خرید شما خالی است و امکان ثبت سفارش وجود ندارد.")

        has_physical_items = any(
            ci.item.delivery_type == Item.DeliveryType.PHYSICAL for ci in cart_items
        )

        # Shipping address validation
        shipping_address = None
        if has_physical_items:
            if not shipping_address_id:
                raise ShippingAddressRequiredError("برای سفارش کالاهای فیزیکی، انتخاب آدرس پستی الزامی است.")
            try:
                shipping_address = Address.objects.get(id=shipping_address_id, user=user)
            except Address.DoesNotExist:
                raise InvalidAddressError("آدرس پستی انتخاب‌شده نامعتبر است یا به شما تعلق ندارد.")

        # Inventory and status verification
        for ci in cart_items:
            item = ci.item
            if item.status != Item.Status.AVAILABLE:
                raise ItemNotAvailableError(f"کالای «{item.title}» دیگر در وضعیت فروش فعال نیست.")
            if not item.is_unlimited_stock and ci.quantity > item.stock:
                raise InsufficientStockError(
                    f"موجودی کالای «{item.title}» تغییر کرده و کمتر از تعداد درخواستی شماست."
                )

        # Calculate totals
        total_items_amount = Decimal("0")
        for ci in cart_items:
            unit_price = ci.item.discount_price if ci.item.discount_price else ci.item.price
            total_items_amount += unit_price * ci.quantity

        discount_amount = Decimal("0")
        applied_coupon = None

        if coupon_code:
            coupon_res = CouponService.validate_and_calculate_discount(
                code=coupon_code,
                user=user,
                cart_items=cart_items,
                total_items_amount=total_items_amount,
            )
            applied_coupon = coupon_res["coupon"]
            discount_amount = coupon_res["discount_amount"]

        total_shipping_cost = Decimal("0")
        # In a production setup, shipping cost is calculated dynamically per vendor shipment
        payable_amount = (total_items_amount + total_shipping_cost) - discount_amount
        if payable_amount < 0:
            payable_amount = Decimal("0")

        # 1. Create Parent Order
        order = Order.objects.create(
            buyer=user,
            order_number=cls.generate_order_number(),
            coupon=applied_coupon,
            total_items_amount=total_items_amount,
            total_shipping_cost=total_shipping_cost,
            discount_amount=discount_amount,
            payable_amount=payable_amount,
            status=Order.Status.PENDING,
            payment_status=Order.PaymentStatus.UNPAID,
            shipping_address=shipping_address,
        )

        # 2. Log Initial Order Status History
        OrderStatusHistory.objects.create(
            order=order,
            from_status="",
            to_status=Order.Status.PENDING,
            changed_by=user,
            note="ثبت سفارش اولیه توسط خریدار",
        )

        # 3. Group Cart Items by Vendor (Multi-Vendor Shipment Architecture)
        items_by_seller: Dict[int, list] = {}
        for ci in cart_items:
            seller_id = ci.item.seller_id
            if seller_id not in items_by_seller:
                items_by_seller[seller_id] = []
            items_by_seller[seller_id].append(ci)

        reservation_expiry = timezone.now() + timedelta(minutes=cls.RESERVATION_MINUTES)

        for seller_id, vendor_items in items_by_seller.items():
            seller = vendor_items[0].item.seller

            # Create an autonomous shipment package for this vendor
            shipment = OrderShipment.objects.create(
                order=order,
                seller=seller,
                shipping_cost=Decimal("0"),
                shipping_method="پست پیشتاز",
                status=OrderShipment.Status.PROCESSING,
            )

            # Record initial shipment status
            ShipmentStatusHistory.objects.create(
                shipment=shipment,
                from_status="",
                to_status=OrderShipment.Status.PROCESSING,
                changed_by=user,
                note="ایجاد بسته مرسوله برای فروشنده",
            )

            # Create OrderItems and apply temporary stock reservation
            for ci in vendor_items:
                item = ci.item
                unit_price = item.discount_price if item.discount_price else item.price

                OrderItem.objects.create(
                    order=order,
                    shipment=shipment,
                    item=item,
                    quantity=ci.quantity,
                    unit_price=unit_price,
                    discount_amount=Decimal("0"),
                )

                # Set temporary reservation to lock inventory against race conditions
                if not item.is_unlimited_stock:
                    item.reserved_until = reservation_expiry
                    item.save(update_fields=["reserved_until"])

        # 4. Empty the user's cart
        CartService.clear_cart(user)

        return order

    @classmethod
    @transaction.atomic
    def confirm_payment_success(cls, order: Order, payment_reference: str = "") -> Order:
        """
        Called upon successful payment gateway webhook or callback verification.
        - Updates Order and Payment status to PAID.
        - Permanently deducts inventory from Item stock.
        - Grants DigitalAccess for digital items.
        - Generates Escrow SellerSettlement records for vendors.
        """
        if order.payment_status == Order.PaymentStatus.PAID:
            return order  # Idempotent: already confirmed

        order.status = Order.Status.PAID
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["status", "payment_status", "updated_at"])

        OrderStatusHistory.objects.create(
            order=order,
            from_status=Order.Status.PENDING,
            to_status=Order.Status.PAID,
            note=f"تایید موفقیت‌آمیز پرداخت بانکی (کد پیگیری: {payment_reference})",
        )

        # Update coupon usage if coupon applied
        if order.coupon:
            CouponService.record_usage(
                coupon=order.coupon,
                user=order.buyer,
                order=order,
                discount_amount=order.discount_amount,
            )

        # Process each vendor shipment
        for shipment in order.shipments.prefetch_related("items__item").all():
            shipment_gross = Decimal("0")

            for order_item in shipment.items.all():
                item = order_item.item

                # 1. Deduct stock permanently and clear reservation
                if not item.is_unlimited_stock:
                    new_stock = max(0, item.stock - order_item.quantity)
                    item.stock = new_stock
                    item.reserved_until = None
                    if new_stock == 0:
                        item.status = Item.Status.COMPLETED
                    item.save(update_fields=["stock", "reserved_until", "status", "updated_at"])

                # 2. Grant digital access if applicable
                if item.delivery_type == Item.DeliveryType.DIGITAL:
                    DigitalAccess.objects.get_or_create(
                        user=order.buyer,
                        item=item,
                        order=order,
                        defaults={
                            "granted_via": DigitalAccess.GrantedVia.PURCHASE,
                            "max_downloads": 10,
                        }
                    )

                shipment_gross += order_item.unit_price * order_item.quantity

            # 3. Create Escrow SellerSettlement
            platform_fee = shipment_gross * cls.PLATFORM_COMMISSION_PERCENT
            net_amount = shipment_gross - platform_fee

            # Retrieve seller verified bank account if available
            primary_bank = shipment.seller.seller_bank_accounts.filter(is_verified=True).first()

            SellerSettlement.objects.create(
                seller=shipment.seller,
                shipment=shipment,
                bank_account=primary_bank,
                gross_amount=shipment_gross,
                platform_fee=platform_fee,
                seller_discount_share=Decimal("0"),
                net_amount=net_amount,
                status=SellerSettlement.Status.HELD,
            )

        return order

    @classmethod
    @transaction.atomic
    def cancel_order(cls, order: Order, reason: str = "لغو به درخواست کاربر یا اتمام مهلت پرداخت") -> Order:
        """
        Cancels an unpaid order and releases any temporary inventory reservations.
        """
        if order.payment_status == Order.PaymentStatus.PAID:
            raise OrderCheckoutError("امکان لغو سفارش پرداخت‌شده از این بخش وجود ندارد.")

        from_status = order.status
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])

        OrderStatusHistory.objects.create(
            order=order,
            from_status=from_status,
            to_status=Order.Status.CANCELLED,
            note=reason,
        )

        # Release stock reservation
        for order_item in order.items.select_related("item").all():
            item = order_item.item
            if item.reserved_until:
                item.reserved_until = None
                item.save(update_fields=["reserved_until"])

        return order
