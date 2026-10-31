from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from .catalog import Item
from .order import Order
from .donation import Donation


class DigitalAccess(models.Model):
    """
    Grants authorized download access for digital goods obtained via purchase or donation.
    Enforces expiration dates and maximum download count caps.
    """
    class GrantedVia(models.TextChoices):
        PURCHASE = "purchase", "خرید نقدی"
        DONATION = "donation", "دریافت اهدایی"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="digital_accesses",
        verbose_name="کاربر مجاز"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="digital_accesses",
        verbose_name="کالای دیجیتال"
    )
    granted_via = models.CharField(
        max_length=20,
        choices=GrantedVia.choices,
        default=GrantedVia.PURCHASE,
        verbose_name="روش اعطای دسترسی"
    )
    order = models.ForeignKey(
        Order,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="digital_accesses",
        verbose_name="سفارش منتهی به خرید"
    )
    donation = models.ForeignKey(
        Donation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="digital_accesses",
        verbose_name="سند اهدای مربوطه"
    )

    download_count = models.PositiveIntegerField(default=0, verbose_name="تعداد دفعات دانلود شده")
    max_downloads = models.PositiveIntegerField(default=5, verbose_name="حداکثر دفعات مجاز دانلود")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضای دسترسی")
    last_downloaded_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین زمان دانلود")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان اعطای دسترسی")

    class Meta:
        db_table = "marketplace_digital_accesses"
        verbose_name = "Digital Access"
        verbose_name_plural = "Digital Accesses"
        constraints = [
            models.UniqueConstraint(fields=["user", "item"], name="unique_user_digital_item")
        ]
        indexes = [
            models.Index(fields=["user"], name="idx_digital_user"),
            models.Index(fields=["item"], name="idx_digital_item"),
        ]

    def __str__(self):
        return f"Access for {self.user} to {self.item.title} ({self.download_count}/{self.max_downloads})"


class Wishlist(models.Model):
    """
    User favorites and wishlist items.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketplace_wishlists",
        verbose_name="کاربر"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
        verbose_name="کالا"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ افزودن به علاقه‌مندی‌ها")

    class Meta:
        db_table = "marketplace_wishlists"
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "item"], name="unique_user_wishlist_item")
        ]
        indexes = [
            models.Index(fields=["user"], name="idx_wishlist_user"),
            models.Index(fields=["item"], name="idx_wishlist_item"),
        ]

    def __str__(self):
        return f"{self.user} -> {self.item.title}"


class Review(models.Model):
    """
    Verified customer reviews and star ratings linked to authenticated orders or donations.
    Prevents fake unverified rating manipulation.
    """
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="کالا"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketplace_reviews",
        verbose_name="ثبت‌کننده نظر"
    )
    order = models.ForeignKey(
        Order,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
        verbose_name="سفارش خرید"
    )
    donation = models.ForeignKey(
        Donation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
        verbose_name="سند اهدا"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="امتیاز (۱ تا ۵ ستاره)"
    )
    comment = models.TextField(blank=True, default="", verbose_name="متن دیدگاه خریدار")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت نظر")

    class Meta:
        db_table = "marketplace_reviews"
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["item", "reviewer"], name="unique_item_reviewer")
        ]
        indexes = [
            models.Index(fields=["item"], name="idx_review_item"),
            models.Index(fields=["rating"], name="idx_review_rating"),
            models.Index(fields=["created_at"], name="idx_review_created_at"),
        ]

    def __str__(self):
        return f"{self.rating}★ by {self.reviewer} on {self.item.title}"
