from django.conf import settings
from django.db import models
from django.db.models import Q

from .base import MarketplaceBaseModel
from .circulation import PhysicalCopy


class UserShelfBook(MarketplaceBaseModel):
    """
    Personal book shelf entry owned by a Tafakor user (قفسه شخصی کتاب کاربر).
    Allows users to register and organize their own books independently of
    whether they want to read, keep privately, share publicly, circulate via QR,
    donate, or sell them.
    """

    class BookFormat(models.TextChoices):
        PHYSICAL = "physical", "نسخه چاپی (فیزیکی)"
        DIGITAL = "digital", "کتاب دیجیتال / الکترونیک"

    class Visibility(models.TextChoices):
        PRIVATE = "private", "خصوصی (فقط خودم)"
        PUBLIC = "public", "عمومی (نمایش در قفسه پروفایل)"

    class ReadingStatus(models.TextChoices):
        IN_SHELF = "in_shelf", "در قفسه کتاب‌ها"
        WANT_TO_READ = "want_to_read", "در لیست مطالعه"
        READING = "reading", "در حال مطالعه"
        FINISHED = "finished", "خوانده‌شده"

    class Disposition(models.TextChoices):
        KEEPING = "keeping", "نگهداری شخصی"
        CIRCULATING = "circulating", "در شبکه گردش (کد QR)"
        FOR_DONATION = "for_donation", "آماده اهدا در بازارچه"
        FOR_SALE = "for_sale", "آماده فروش در بازارچه"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="shelf_books",
        verbose_name="مالک کتاب در قفسه",
    )
    book_title = models.ForeignKey(
        "marketplace.BookTitle",
        on_delete=models.PROTECT,
        related_name="shelf_entries",
        verbose_name="شناسنامه کتاب",
    )

    book_format = models.CharField(
        max_length=20,
        choices=BookFormat.choices,
        default=BookFormat.PHYSICAL,
        db_index=True,
        verbose_name="قالب نسخه",
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        db_index=True,
        verbose_name="سطح نمایش",
    )
    reading_status = models.CharField(
        max_length=20,
        choices=ReadingStatus.choices,
        default=ReadingStatus.IN_SHELF,
        db_index=True,
        verbose_name="وضعیت مطالعه",
    )
    disposition = models.CharField(
        max_length=20,
        choices=Disposition.choices,
        default=Disposition.KEEPING,
        db_index=True,
        verbose_name="وضعیت عرضه یا نگهداری",
    )

    condition = models.CharField(
        max_length=20,
        choices=PhysicalCopy.Condition.choices,
        null=True,
        blank=True,
        verbose_name="کیفیت ظاهری نسخه چاپی",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد جلد در قفسه",
    )
    reserved_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد جلد رزروشده برای اهدا یا انتقال",
    )
    gifted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gifted_shelf_books",
        verbose_name="اهداکننده این کتاب (در صورت دریافتی بودن)",
    )
    is_gift = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="آیا این کتاب به عنوان هدیه دریافت شده است؟",
    )
    personal_note = models.TextField(
        blank=True,
        default="",
        verbose_name="یادداشت شخصی کاربر",
    )
    digital_reference = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="مشخصات یا محل فایل دیجیتال (اختیاری)",
    )
    acquired_from = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="نحوه تهیه / منبع",
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="امتیاز شخصی (۱ تا ۵)",
    )

    # Optional donation delivery/handover configuration
    donation_methods = models.JSONField(
        default=list,
        blank=True,
        verbose_name="انواع روش‌های اهدا",
    )
    preferred_station = models.ForeignKey(
        "marketplace.BookStation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shelf_books",
        verbose_name="ایستگاه یا قفسه منتخب",
    )
    shipping_payer = models.CharField(
        max_length=20,
        blank=True,
        default="recipient",
        verbose_name="پرداخت‌کننده هزینه ارسال پستی",
    )

    # Optional links activated ONLY when the user decides to circulate, donate, or sell
    physical_copy = models.OneToOneField(
        "marketplace.PhysicalCopy",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shelf_book",
        verbose_name="نسخه متصل در گردش QR",
    )
    marketplace_item = models.OneToOneField(
        "marketplace.Item",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shelf_book",
        verbose_name="آگهی متصل در بازارچه",
    )

    class Meta:
        db_table = "marketplace_user_shelf_books"
        verbose_name = "User Shelf Book"
        verbose_name_plural = "User Shelf Books"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(rating__isnull=True) | (Q(rating__gte=1) & Q(rating__lte=5)),
                name="chk_shelf_book_rating_1_to_5",
            ),
            models.CheckConstraint(
                check=Q(quantity__gte=0),
                name="chk_shelf_book_quantity_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "deleted_at", "-created_at"], name="idx_shelf_user_created"),
            models.Index(fields=["user", "visibility", "deleted_at"], name="idx_shelf_user_vis"),
            models.Index(fields=["user", "disposition"], name="idx_shelf_user_disp"),
            models.Index(fields=["reading_status"], name="idx_shelf_reading_st"),
            models.Index(fields=["book_format"], name="idx_shelf_book_fmt"),
        ]

    def __str__(self):
        return f"{self.book_title.title} ({self.user})"

    @property
    def available_quantity(self) -> int:
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def can_donate(self) -> bool:
        if self.is_gift:
            return False
        return self.available_quantity > 0

    def get_effective_donation_methods(self) -> list[str]:
        """Returns normalized handover/donation methods for display & publishing."""
        from .catalog import Item

        if self.disposition == self.Disposition.CIRCULATING:
            return [Item.DonationMethod.IN_PERSON]
        if self.disposition != self.Disposition.FOR_DONATION:
            return []
        if self.book_format == self.BookFormat.DIGITAL:
            return [Item.DonationMethod.DIGITAL]
        return Item.normalize_donation_methods(
            self.donation_methods,
            delivery_type=Item.DeliveryType.PHYSICAL,
            has_station=bool(self.preferred_station_id),
            has_physical_copy=bool(self.physical_copy_id),
        )
