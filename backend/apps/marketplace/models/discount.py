from django.db import models
from django.conf import settings


class Coupon(models.Model):
    """
    Promotional coupons with percentage or fixed amount discounts,
    usage limits, minimum order values, and seller/platform cost-sharing.
    """
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "درصدی"
        FIXED_AMOUNT = "fixed_amount", "مبلغ ثابت (تومان)"

    class DiscountBearer(models.TextChoices):
        PLATFORM = "platform", "پلتفرم تفاخر"
        SELLER = "seller", "فروشنده کالا"

    code = models.CharField(max_length=50, unique=True, verbose_name="کد کوپن")
    title = models.CharField(max_length=150, blank=True, default="", verbose_name="عنوان تبلیغاتی")
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        verbose_name="نوع تخفیف"
    )
    discount_value = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="مقدار تخفیف (درصد یا تومان)"
    )
    max_discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="سقف تخفیف برای کدهای درصدی (تومان)"
    )
    min_order_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="حداقل ارزش سبد خرید جهت اعمال کوپن"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="marketplace_coupons",
        verbose_name="فروشنده خاص (اگر خالی باشد، سراسری است)"
    )
    discount_bearer = models.CharField(
        max_length=20,
        choices=DiscountBearer.choices,
        default=DiscountBearer.PLATFORM,
        verbose_name="متقبل تخفیف (پلتفرم یا فروشنده)"
    )
    usage_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name="سقف کل دفعات استفاده")
    user_usage_limit = models.PositiveIntegerField(default=1, verbose_name="سقف استفاده به ازای هر کاربر")
    used_count = models.PositiveIntegerField(default=0, verbose_name="تعداد دفعات استفاده شده تاکنون")

    valid_from = models.DateTimeField(verbose_name="تاریخ شروع اعتبار")
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پایان اعتبار")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        db_table = "marketplace_coupons"
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        indexes = [
            models.Index(fields=["code"], name="idx_coupon_code"),
            models.Index(fields=["is_active"], name="idx_coupon_is_active"),
            models.Index(fields=["seller"], name="idx_coupon_seller"),
        ]

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"


class CouponUsage(models.Model):
    """
    Audit log of coupon redemptions per user and order to enforce usage limits.
    """
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages",
        verbose_name="کوپن"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        verbose_name="کاربر استفاده‌کننده"
    )
    order = models.ForeignKey(
        'marketplace.Order',
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        verbose_name="سفارش مربوطه"
    )
    discount_applied = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="مبلغ تخفیف اعمال‌شده"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ مصرف")

    class Meta:
        db_table = "marketplace_coupon_usages"
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        constraints = [
            models.UniqueConstraint(fields=["coupon", "user", "order"], name="unique_coupon_user_order")
        ]
        indexes = [
            models.Index(fields=["coupon"], name="idx_coupon_usage_coupon"),
            models.Index(fields=["user"], name="idx_coupon_usage_user"),
        ]

    def __str__(self):
        return f"{self.user} used {self.coupon.code} on Order #{self.order_id}"
