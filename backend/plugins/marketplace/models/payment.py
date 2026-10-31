from django.db import models
from django.conf import settings
from .order import Order, OrderShipment
from .finance import SellerBankAccount


class Payment(models.Model):
    """
    Financial gateway transaction tracking records with raw payloads for auditing.
    """
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        SUCCESSFUL = "successful", "پرداخت موفق"
        FAILED = "failed", "پرداخت ناموفق"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="سفارش مربوطه"
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="مبلغ تراکنش (تومان)"
    )
    gateway = models.CharField(
        max_length=50,
        blank=True,
        default="zarinpal",
        verbose_name="درگاه بانکی (زرین‌پال، سداد و...)"
    )
    authority = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name="شناسه پیگیری درگاه (Authority / Token)"
    )
    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="شماره مرجع بانکی (RefID)"
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="وضعیت تراکنش"
    )
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="پاسخ کامل وب‌سرویس بانک (جهت ممیزی مالی)"
    )
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تایید تراکنش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")

    class Meta:
        db_table = "marketplace_payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order"], name="idx_payment_order"),
            models.Index(fields=["status"], name="idx_payment_status"),
            models.Index(fields=["authority"], name="idx_payment_authority"),
            models.Index(fields=["paid_at"], name="idx_payment_paid_at"),
        ]

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order.order_number}: {self.amount:,} Toman ({self.get_status_display()})"


class SellerSettlement(models.Model):
    """
    Escrow accounting record holding vendor funds until shipment delivery confirmation.
    Safeguards buyers from fraud and calculates platform commissions.
    """
    class Status(models.TextChoices):
        HELD = "held", "امانت نزد پلتفرم (در انتظار تحویل بسته)"
        APPROVED = "approved", "تایید شده برای تسویه پایا"
        SETTLED = "settled", "تسویه نهایی و واریز شد"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="settlements",
        verbose_name="فروشنده"
    )
    shipment = models.OneToOneField(
        OrderShipment,
        on_delete=models.CASCADE,
        related_name="settlement",
        verbose_name="محموله مربوطه"
    )
    bank_account = models.ForeignKey(
        SellerBankAccount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="settlements",
        verbose_name="حساب بانکی واریز"
    )

    gross_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="مبلغ کل فروش بسته (تومان)"
    )
    platform_fee = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="کارمزد پلتفرم تفاخر (تومان)"
    )
    seller_discount_share = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="سهم تخفیف متقبل‌شده توسط فروشنده (تومان)"
    )
    net_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="مبلغ خالص واریزی به حساب فروشنده (تومان)"
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.HELD,
        verbose_name="وضعیت امانت‌داری و تسویه"
    )
    settled_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ واریز بانکی")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد رکورد")

    class Meta:
        db_table = "marketplace_seller_settlements"
        verbose_name = "Seller Settlement"
        verbose_name_plural = "Seller Settlements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["seller"], name="idx_settle_seller"),
            models.Index(fields=["status"], name="idx_settle_status"),
            models.Index(fields=["settled_at"], name="idx_settle_settled_at"),
            models.Index(fields=["created_at"], name="idx_settle_created_at"),
        ]

    def __str__(self):
        return f"Settlement #{self.id} for {self.seller}: {self.net_amount:,} Toman ({self.get_status_display()})"
