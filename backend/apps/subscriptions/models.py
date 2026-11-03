from django.db import models
from django.conf import settings
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """
    تعریف طرح‌ها و بسته‌های اشتراکی به تفکیک پلاگین (قرآن، گلشن راز و...)
    و تطابق آن با شناسه محصول (SKU) در کافه‌بازار
    """
    plugin_identifier = models.CharField(
        max_length=100,
        db_index=True,
        help_text="شناسه پلاگین هدف مانند quran یا golshan_raz یا all برای پلن‌های مشترک"
    )
    sku = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        help_text="شناسه محصول در کافه‌بازار (SKU) مانند quran_vip_1m"
    )
    title = models.CharField(
        max_length=255,
        help_text="عنوان نمایشی بسته (مثلاً اشتراک ۱ ماهه قرآن ویژه)"
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="توضیحات و امکانات بسته"
    )
    duration_days = models.PositiveIntegerField(
        default=30,
        help_text="مدت اعتبار اشتراک به روز"
    )
    price = models.BigIntegerField(
        default=0,
        help_text="مبلغ بسته به ریال (جهت آمار، حسابداری و فاکتور)"
    )
    features = models.JSONField(
        default=dict,
        blank=True,
        help_text="امکانات یا محدودیت‌های ویژه بسته (اختیاری)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="آیا این بسته هم‌اکنون برای خرید فعال است؟"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tafakor_subscription_plans'
        ordering = ['plugin_identifier', 'duration_days', 'price']
        verbose_name = 'طرح اشتراک'
        verbose_name_plural = 'طرح‌های اشتراک'

    def __str__(self):
        return f"{self.title} ({self.plugin_identifier} - {self.sku})"


class UserSubscription(models.Model):
    """
    شناسنامه وضعیت دسترسی و اشتراک فعال یا منقضی‌شده کاربران
    """
    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('expired', 'منقضی‌شده'),
        ('revoked', 'لغو شده / بازپس‌گرفته'),
    ]

    SOURCE_CHOICES = [
        ('cafebazaar', 'کافه‌بازار'),
        ('myket', 'مایکت'),
        ('direct', 'درگاه مستقیم'),
        ('gift', 'هدیه ادمین'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text="کاربر دارنده اشتراک"
    )
    plugin_identifier = models.CharField(
        max_length=100,
        db_index=True,
        help_text="شناسه افزونه‌ای که دسترسی آن باز شده (quran، golshan_raz، یا all)"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_subscriptions',
        help_text="آخرین طرح خریداری‌شده"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(db_index=True, help_text="زمان دقیق پایان دسترسی")
    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        default='cafebazaar',
        help_text="مبدأ خرید و پرداخت"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tafakor_user_subscriptions'
        ordering = ['-expires_at']
        indexes = [
            models.Index(fields=['user', 'plugin_identifier', 'status', 'expires_at']),
        ]
        verbose_name = 'اشتراک کاربر'
        verbose_name_plural = 'اشتراک‌های کاربران'

    def __str__(self):
        return f"{self.user} - {self.plugin_identifier} ({self.status}) تا {self.expires_at.strftime('%Y/%m/%d')}"

    @property
    def is_currently_valid(self) -> bool:
        """بررسی اعتبار زمانی و وضعیتی اشتراک"""
        return self.status == 'active' and self.expires_at > timezone.now()


class PurchaseVerificationLog(models.Model):
    """
    ثبت گزارش و لاگ یکتای توکن‌های خرید کافه‌بازار جهت جلوگیری از سوءاستفاده
    و اعتبارسنجی مجدد
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchase_logs',
        help_text="کاربری که ادعای خرید کرده"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_logs'
    )
    sku = models.CharField(
        max_length=150,
        db_index=True,
        help_text="شناسه بسته کافه‌بازار"
    )
    purchase_token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="توکن خرید یکتای دریافتی از کافه‌بازار (جلوگیری از Replay Attack)"
    )
    marketplace = models.CharField(
        max_length=50,
        default='cafebazaar'
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="آیا از سمت سرور بازار رسماً تایید شد؟"
    )
    bazaar_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="پاسخ کامل و خام دریافتی از وب‌سرویس کافه‌بازار"
    )
    verification_error = models.TextField(
        blank=True,
        default='',
        help_text="متن خطای بازگشتی بازار در صورت عدم تایید"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tafakor_purchase_verification_logs'
        ordering = ['-created_at']
        verbose_name = 'گزارش وریفای خرید'
        verbose_name_plural = 'گزارش‌های وریفای خرید'

    def __str__(self):
        status_str = "تایید شد" if self.is_verified else "رد شد"
        return f"خرید {self.sku} توسط {self.user} ({status_str})"

