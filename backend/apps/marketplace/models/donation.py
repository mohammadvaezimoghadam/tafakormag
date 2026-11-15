from django.db import models
from django.conf import settings
from .catalog import Item
from .location import Address


class DonationRequest(models.Model):
    """
    Prospective recipients submit requests explaining why they need a donated item.
    """
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار تصمیم اهداکننده"
        ACCEPTED = "accepted", "پذیرفته شده"
        REJECTED = "rejected", "رد شده"
        CANCELLED = "cancelled", "انصراف متقاضی"

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="donation_requests",
        verbose_name="کالای اهدایی"
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_donation_requests",
        verbose_name="متقاضی دریافت"
    )
    message = models.TextField(blank=True, default="", verbose_name="پیام یا توضیح متقاضی به اهداکننده")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="وضعیت درخواست"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت درخواست")

    class Meta:
        db_table = "marketplace_donation_requests"
        verbose_name = "Donation Request"
        verbose_name_plural = "Donation Requests"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["item", "requester"], name="unique_item_requester")
        ]
        indexes = [
            models.Index(fields=["status"], name="idx_don_req_status"),
            models.Index(fields=["created_at"], name="idx_don_req_created_at"),
        ]

    def __str__(self):
        return f"Request by {self.requester} for {self.item.title} ({self.get_status_display()})"


class Donation(models.Model):
    """
    Confirmed peer-to-peer (C2C) donation transaction with physical shipping tracking or digital fulfillment.
    """
    class Status(models.TextChoices):
        ACCEPTED = "accepted", "پذیرفته شده و در انتظار ارسال"
        SHIPPED = "shipped", "ارسال شده با پست"
        DELIVERED = "delivered", "تحویل قطعی به گیرنده"
        CANCELLED = "cancelled", "لغو شده"

    class ShippingPayer(models.TextChoices):
        DONOR = "donor", "پرداخت توسط اهداکننده"
        RECIPIENT = "recipient", "پرداخت توسط دریافت‌کننده (پس‌کرایه)"

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="donations",
        verbose_name="کالای اهدایی"
    )
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="donations_given",
        verbose_name="اهداکننده"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="donations_received",
        verbose_name="دریافت‌کننده"
    )
    donation_request = models.ForeignKey(
        DonationRequest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="donation",
        verbose_name="درخواست مبدا"
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACCEPTED,
        verbose_name="وضعیت اهدا"
    )
    shipping_address = models.ForeignKey(
        Address,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="donations",
        verbose_name="آدرس پستی گیرنده"
    )
    shipping_payer = models.CharField(
        max_length=20,
        choices=ShippingPayer.choices,
        default=ShippingPayer.RECIPIENT,
        verbose_name="پرداخت‌کننده هزینه پست"
    )
    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="کد رهگیری پستی"
    )

    accepted_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ پذیرش")
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ ارسال")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تحویل")

    class Meta:
        db_table = "marketplace_donations"
        verbose_name = "Donation"
        verbose_name_plural = "Donations"
        ordering = ["-accepted_at"]
        indexes = [
            models.Index(fields=["donor"], name="idx_donation_donor"),
            models.Index(fields=["recipient"], name="idx_donation_recipient"),
            models.Index(fields=["status"], name="idx_donation_status"),
            models.Index(fields=["accepted_at"], name="idx_donation_accepted_at"),
        ]

    def __str__(self):
        return f"Donation #{self.id}: {self.item.title} to {self.recipient}"
