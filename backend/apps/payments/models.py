import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class PaymentTransaction(models.Model):
    """
    Centralized financial payment ledger unifying gateway initiation, verification,
    audit payloads, and idempotent settlement state across all Tafakor domains.
    """

    class Gateway(models.TextChoices):
        ZARINPAL = "zarinpal", "زرین‌پال"
        FREE = "free", "تراکنش رایگان (بدون درگاه)"

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        VERIFIED = "verified", "تاییدشده در بانک (در انتظار تکمیل دامنه)"
        SUCCESSFUL = "successful", "پرداخت و تکمیل موفق"
        FAILED = "failed", "پرداخت ناموفق"
        CANCELLED = "cancelled", "لغوشده توسط کاربر"

    class Purpose(models.TextChoices):
        DONATION = "donation", "حمایت از پویش نیکوکاری"
        MARKETPLACE_ORDER = "marketplace_order", "سفارش فروشگاه و کتاب"
        SUBSCRIPTION = "subscription", "اشتراک پلتفرم"
        OTHER = "other", "سایر"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payment_transactions",
        verbose_name="کاربر پرداخت‌کننده",
    )
    purpose = models.CharField(
        max_length=40,
        choices=Purpose.choices,
        default=Purpose.OTHER,
        db_index=True,
        verbose_name="موضوع پرداخت",
    )
    reference_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="شناسه رکورد مرتبط (سفارش/پویش)",
    )

    amount = models.BigIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="مبلغ (تومان)",
    )
    currency = models.CharField(max_length=10, default="IRT", verbose_name="واحد پول")
    gateway = models.CharField(
        max_length=30,
        choices=Gateway.choices,
        default=Gateway.ZARINPAL,
        db_index=True,
        verbose_name="درگاه پرداخت",
    )
    authority = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        verbose_name="شناسه پیگیری درگاه (Authority)",
    )
    ref_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
        db_index=True,
        verbose_name="شماره مرجع بانکی (RefID)",
    )
    tracking_code = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="کد رهگیری",
    )
    card_pan = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="شماره کارت ماسک‌شده",
    )
    fee = models.BigIntegerField(null=True, blank=True, verbose_name="کارمزد درگاه")

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="وضعیت تراکنش",
    )
    description = models.CharField(max_length=255, blank=True, default="", verbose_name="توضیحات")
    callback_url = models.URLField(max_length=500, blank=True, default="", verbose_name="آدرس بازگشت درگاه")
    client_redirect_url = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="مسیر ریدایرکت نهایی کلاینت یا دیپ‌لینک",
    )

    metadata = models.JSONField(default=dict, blank=True, verbose_name="متادیتای دامنه")
    raw_request = models.JSONField(default=dict, blank=True, verbose_name="پاسخ شروع درگاه")
    raw_verify_response = models.JSONField(default=dict, blank=True, verbose_name="پاسخ تایید درگاه")
    failure_reason = models.TextField(blank=True, default="", verbose_name="علت خطا یا لغو")

    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تایید بانک")
    settled_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تکمیل نهایی دامنه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        db_table = "payments_transactions"
        verbose_name = "تراکنش پرداخت"
        verbose_name_plural = "تراکنش‌های پرداخت"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["purpose", "reference_id"], name="idx_pay_purpose_ref"),
            models.Index(fields=["status", "created_at"], name="idx_pay_status_created"),
            models.Index(fields=["user", "created_at"], name="idx_pay_user_created"),
            models.Index(fields=["authority"], name="idx_pay_authority"),
        ]

    def __str__(self) -> str:
        return f"PaymentTransaction({self.purpose}:{self.reference_id} | {self.amount} {self.currency} | {self.status})"

