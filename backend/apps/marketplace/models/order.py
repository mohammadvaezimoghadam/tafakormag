from django.db import models
from django.conf import settings
from .base import TimeStampedModel, MarketplaceBaseModel
from .location import Address
from .catalog import Item
from .discount import Coupon


class Order(MarketplaceBaseModel):
    """
    Parent order placed by a buyer. May encompass multiple separate seller shipments.
    """
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        PAID = "paid", "پرداخت شده"
        PROCESSING = "processing", "در حال آماده‌سازی و ارسال"
        COMPLETED = "completed", "تکمیل و تحویل شده"
        CANCELLED = "cancelled", "لغو شده"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "پرداخت نشده"
        PAID = "paid", "پرداخت موفق"
        REFUNDED = "refunded", "مسترد شده"

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marketplace_orders",
        verbose_name="خریدار"
    )
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="شماره سفارش اختصاصی"
    )
    coupon = models.ForeignKey(
        Coupon,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
        verbose_name="کوپن تخفیف اعمال‌شده"
    )

    total_items_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="جمع مبالغ اقلام (تومان)"
    )
    total_shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="مجموع هزینه ارسال بسته‌ها (تومان)"
    )
    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="مبلغ کل تخفیف (تومان)"
    )
    payable_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="مبلغ نهایی قابل پرداخت (تومان)"
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="وضعیت سفارش"
    )
    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name="وضعیت پرداخت"
    )

    shipping_address = models.ForeignKey(
        Address,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
        verbose_name="آدرس تحویل گیرنده"
    )

    class Meta:
        db_table = "marketplace_orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["buyer"], name="idx_order_buyer"),
            models.Index(fields=["status"], name="idx_order_status"),
            models.Index(fields=["payment_status"], name="idx_order_payment_status"),
            models.Index(fields=["order_number"], name="idx_order_number"),
            models.Index(fields=["created_at"], name="idx_order_created_at"),
        ]

    def __str__(self):
        return f"Order #{self.order_number} ({self.get_status_display()})"


class OrderShipment(TimeStampedModel):
    """
    Sub-package per distinct vendor within an order, with autonomous tracking and delivery states.
    """
    class Status(models.TextChoices):
        PROCESSING = "processing", "در حال بسته‌بندی توسط فروشنده"
        SHIPPED = "shipped", "تحویل به پست / ارسال شده"
        DELIVERED = "delivered", "تحویل داده شده به خریدار"
        DISPUTE = "dispute", "دارای اختلاف / در حال داوری"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="shipments",
        verbose_name="سفارش مادر"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marketplace_shipments",
        verbose_name="فروشنده این محموله"
    )

    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="هزینه پست این محموله (تومان)"
    )
    shipping_method = models.CharField(
        max_length=50,
        blank=True,
        default="پست پیشتاز",
        verbose_name="روش ارسال (پست پیشتاز، تیپاکس، پیک)"
    )
    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="کد رهگیری پستی مرسوله"
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PROCESSING,
        verbose_name="وضعیت محموله"
    )
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تحویل به پست")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تحویل به مشتری")

    class Meta:
        db_table = "marketplace_order_shipments"
        verbose_name = "Order Shipment"
        verbose_name_plural = "Order Shipments"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["order"], name="idx_shipment_order"),
            models.Index(fields=["seller"], name="idx_shipment_seller"),
            models.Index(fields=["status"], name="idx_shipment_status"),
        ]

    def __str__(self):
        return f"Shipment #{self.id} for Order #{self.order.order_number} by {self.seller}"


class OrderItem(TimeStampedModel):
    """
    Line items within an order linked directly to their responsible shipment package.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سفارش"
    )
    shipment = models.ForeignKey(
        OrderShipment,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="بسته مرسوله مربوطه"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="کالای خریداری‌شده"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="قیمت واحد قطعی در زمان خرید (تومان)"
    )
    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="تخفیف واحد (تومان)"
    )

    class Meta:
        db_table = "marketplace_order_items"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        indexes = [
            models.Index(fields=["order"], name="idx_order_item_order"),
            models.Index(fields=["shipment"], name="idx_order_item_shipment"),
            models.Index(fields=["item"], name="idx_order_item_item"),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.item.title} (Order #{self.order.order_number})"


class OrderStatusHistory(models.Model):
    """
    Audit timeline tracking changes to parent order statuses.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="سفارش"
    )
    from_status = models.CharField(max_length=30, blank=True, default="", verbose_name="وضعیت قبلی")
    to_status = models.CharField(max_length=30, verbose_name="وضعیت جدید")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="تغییر دهنده (خالی = سیستمی)"
    )
    note = models.TextField(blank=True, default="", verbose_name="توضیحات و علت تغییر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت رویداد")

    class Meta:
        db_table = "marketplace_order_status_histories"
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order"], name="idx_ord_hist_order"),
            models.Index(fields=["to_status"], name="idx_ord_hist_to_status"),
            models.Index(fields=["created_at"], name="idx_ord_hist_created_at"),
        ]

    def __str__(self):
        return f"Order #{self.order.order_number}: {self.from_status} -> {self.to_status}"


class ShipmentStatusHistory(models.Model):
    """
    Audit timeline tracking changes to individual shipment statuses.
    """
    shipment = models.ForeignKey(
        OrderShipment,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="محموله"
    )
    from_status = models.CharField(max_length=30, blank=True, default="", verbose_name="وضعیت قبلی")
    to_status = models.CharField(max_length=30, verbose_name="وضعیت جدید")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="تغییر دهنده (خالی = سیستمی)"
    )
    note = models.TextField(blank=True, default="", verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت رویداد")

    class Meta:
        db_table = "marketplace_shipment_status_histories"
        verbose_name = "Shipment Status History"
        verbose_name_plural = "Shipment Status Histories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shipment"], name="idx_ship_hist_shipment"),
            models.Index(fields=["to_status"], name="idx_ship_hist_to_status"),
            models.Index(fields=["created_at"], name="idx_ship_hist_created_at"),
        ]

    def __str__(self):
        return f"Shipment #{self.shipment_id}: {self.from_status} -> {self.to_status}"
