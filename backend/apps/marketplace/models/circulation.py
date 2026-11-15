import uuid
import secrets
from django.db import models
from django.db.models import Q
from django.conf import settings
from apps.notes.models import normalize_persian_text
from .base import TimeStampedModel, MarketplaceBaseModel
from .location import City


class BookTitle(MarketplaceBaseModel):
    """
    Master book catalog reference entity (شناسنامه مرجع عنوان کتاب).
    Shared across commercial marketplace listings and physical circulation.
    100% self-contained with automatic Persian text normalization.
    """
    class Source(models.TextChoices):
        MANUAL = "manual", "ثبت دستی کاربر"
        ADMIN = "admin", "ثبت رسمی مدیریت"
        SEED = "seed", "بارگذاری اولیه سیستمی"

    title = models.CharField(max_length=255, db_index=True, verbose_name="عنوان کتاب")
    normalized_title = models.CharField(max_length=255, db_index=True, editable=False, verbose_name="عنوان نرمال‌شده")
    author = models.CharField(max_length=150, db_index=True, verbose_name="نویسنده / پدیدآور")
    normalized_author = models.CharField(max_length=150, db_index=True, editable=False, verbose_name="نویسنده نرمال‌شده")
    translator = models.CharField(max_length=150, blank=True, default="", db_index=True, verbose_name="مترجم یا مصحح")
    normalized_translator = models.CharField(max_length=150, blank=True, default="", db_index=True, editable=False, verbose_name="مترجم نرمال‌شده")
    publisher = models.CharField(max_length=150, blank=True, default="", db_index=True, verbose_name="ناشر")
    category = models.CharField(max_length=100, blank=True, default="", db_index=True, verbose_name="دسته‌بندی موضوعی")
    isbn = models.CharField(max_length=25, blank=True, null=True, db_index=True, verbose_name="شابک (ISBN)")
    publication_year = models.IntegerField(null=True, blank=True, verbose_name="سال چاپ")
    edition = models.CharField(max_length=50, blank=True, default="", verbose_name="نوبت چاپ")
    description = models.TextField(blank=True, default="", verbose_name="خلاصه و معرفی کتاب")
    cover_image = models.FileField(upload_to="marketplace/book_titles/covers/", null=True, blank=True, verbose_name="تصویر رسمی جلد")
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL, verbose_name="منبع ورود اطلاعات")
    verified_by_admin = models.BooleanField(default=False, db_index=True, verbose_name="تایید شده توسط مدیریت")

    class Meta:
        db_table = "marketplace_book_titles"
        verbose_name = "Book Title"
        verbose_name_plural = "Book Titles"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["normalized_title"], name="idx_book_norm_title"),
            models.Index(fields=["normalized_author"], name="idx_book_norm_author"),
            models.Index(fields=["normalized_translator"], name="idx_book_norm_trans"),
            models.Index(fields=["isbn"], name="idx_book_title_isbn"),
            models.Index(fields=["category"], name="idx_book_title_cat"),
        ]

    def save(self, *args, **kwargs):
        self.normalized_title = normalize_persian_text(self.title or "").strip()
        self.normalized_author = normalize_persian_text(self.author or "").strip()
        self.normalized_translator = normalize_persian_text(self.translator or "").strip()
        super().save(*args, **kwargs)

    def __str__(self):
        parts = [self.title, f"اثر {self.author}"]
        if self.translator:
            parts.append(f"ترجمه {self.translator}")
        return " - ".join(parts)


class BookStation(TimeStampedModel):
    """
    Physical book kiosk or shelf (ایستگاه یا قفسه فیزیکی تفاخر).
    Installed in universities, mosques, metro stations, cultural centers.
    """
    name = models.CharField(max_length=150, verbose_name="نام ایستگاه / قفسه")
    city = models.ForeignKey(
        City,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="book_stations",
        verbose_name="شهر"
    )
    address_text = models.TextField(verbose_name="نشانی دقیق محل استقرار")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="عرض جغرافیایی")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="طول جغرافیایی")
    capacity = models.PositiveIntegerField(default=20, verbose_name="ظرفیت کل قفسه (تعداد جلد)")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="فعال")

    class Meta:
        db_table = "marketplace_book_stations"
        verbose_name = "Book Station"
        verbose_name_plural = "Book Stations"
        ordering = ["city", "name"]
        indexes = [
            models.Index(fields=["is_active"], name="idx_station_is_active"),
            models.Index(fields=["city", "is_active"], name="idx_station_city_active"),
        ]

    def __str__(self):
        city_name = self.city.name if self.city else "نامشخص"
        return f"{self.name} ({city_name})"

    @property
    def current_books_count(self) -> int:
        if hasattr(self, "_current_books_count"):
            return self._current_books_count
        return self.books_on_shelf.filter(status=PhysicalCopy.Status.IN_STATION).count()

    @current_books_count.setter
    def current_books_count(self, value: int):
        self._current_books_count = value


class PhysicalCopy(MarketplaceBaseModel):
    """
    Specific physical copy of a book with unique short code and QR identity.
    (جلد فیزیکی کتاب در گردش)
    """
    class Status(models.TextChoices):
        ACTIVE = "active", "فعال و نزد کاربر"
        TRANSFERRING = "transferring", "در حال انتقال حضوری"
        IN_STATION = "in_station", "موجود در قفسه تفاخر"
        LOST = "lost", "گزارش مفقودی"
        RETIRED = "retired", "بایگانی شخصی / خارج شده از چرخه"

    class Condition(models.TextChoices):
        NEW = "new", "نو و آکبند"
        LIKE_NEW = "like_new", "در حد نو"
        GOOD = "good", "دست دوم سالم"
        FAIR = "fair", "خوانده‌شده با حاشیه‌نویسی"
        WORN = "worn", "کهنه یا آسیب‌دیده"

    class Privacy(models.TextChoices):
        PUBLIC_NAME = "public_name", "نمایش نام و نام‌خانوادگی"
        FIRST_NAME_ONLY = "first_name_only", "فقط نام کوچک"
        ANONYMOUS = "anonymous", "یک همراه ناشناس تفاخر"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_code = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        verbose_name="کد کوتاه اختصاصی (برای QR و ورود دستی)"
    )
    book_title = models.ForeignKey(
        BookTitle,
        on_delete=models.PROTECT,
        related_name="physical_copies",
        verbose_name="عنوان مرجع کتاب"
    )
    current_holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="held_book_copies",
        verbose_name="نگهدارنده / دارنده فعلی"
    )
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="registered_book_copies",
        verbose_name="ثبت‌کننده اولیه در سیستم"
    )
    original_donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="initially_donated_copies",
        verbose_name="اولین اهداکننده کتاب"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name="وضعیت گردش"
    )
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
        verbose_name="کیفیت ظاهری نسخه"
    )
    station = models.ForeignKey(
        BookStation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="books_on_shelf",
        verbose_name="قفسه / ایستگاه محل استقرار"
    )
    transfer_count = models.PositiveIntegerField(default=0, verbose_name="تعداد دفعات انتقال و گردش")
    privacy = models.CharField(
        max_length=20,
        choices=Privacy.choices,
        default=Privacy.FIRST_NAME_ONLY,
        verbose_name="حریم خصوصی نمایش نام در سفرنامه"
    )

    class Meta:
        db_table = "marketplace_physical_copies"
        verbose_name = "Physical Book Copy"
        verbose_name_plural = "Physical Book Copies"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["short_code"], name="idx_copy_short_code"),
            models.Index(fields=["status"], name="idx_copy_status"),
            models.Index(fields=["current_holder", "status"], name="idx_copy_holder_status"),
            models.Index(fields=["station", "status"], name="idx_copy_station_status"),
        ]

    def __str__(self):
        return f"{self.book_title.title} [{self.short_code}]"

    @classmethod
    def generate_unique_short_code(cls) -> str:
        """Generates a human-friendly collision-resistant short code like TK-8492"""
        prefix = "TK"
        alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
        for _ in range(20):
            code_suffix = "".join(secrets.choice(alphabet) for _ in range(4))
            candidate = f"{prefix}-{code_suffix}"
            if not cls.objects.filter(short_code=candidate).exists():
                return candidate
        return f"{prefix}-{uuid.uuid4().hex[:5].upper()}"


class Transfer(TimeStampedModel):
    """
    Immutable handover transaction logging every movement of a PhysicalCopy (سفرنامه کتاب).
    """
    class Method(models.TextChoices):
        SCAN_CONFIRM = "scan_confirm", "اسکن و تایید دوطرفه حضوری"
        OTP_FALLBACK = "otp_fallback", "انتقال با کد تایید موقت ۴ رقمی"
        STATION_DEPOSIT = "station_deposit", "تحویل به قفسه تفاخر"
        STATION_PICKUP = "station_pickup", "برداشت از قفسه تفاخر"
        POSTAL = "postal", "ارسال با پست"

    class Status(models.TextChoices):
        PENDING_DONOR = "pending_donor", "در انتظار تایید اهداکننده"
        PENDING_RECIPIENT = "pending_recipient", "در انتظار تایید گیرنده"
        CONFIRMED = "confirmed", "تایید شده و انتقال قطعی"
        CANCELLED = "cancelled", "لغو شده"
        EXPIRED = "expired", "منقضی‌شده"

    copy = models.ForeignKey(
        PhysicalCopy,
        on_delete=models.CASCADE,
        related_name="transfers",
        verbose_name="نسخه فیزیکی کتاب"
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="given_transfers",
        verbose_name="اهداکننده / واگذارکننده"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="received_transfers",
        verbose_name="گیرنده جدید"
    )
    station = models.ForeignKey(
        BookStation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="station_transfers",
        verbose_name="قفسه مربوطه (در صورت انتقال ایستگاهی)"
    )
    method = models.CharField(
        max_length=25,
        choices=Method.choices,
        default=Method.SCAN_CONFIRM,
        verbose_name="شیوه انتقال"
    )
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.CONFIRMED,
        db_index=True,
        verbose_name="وضعیت انتقال"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد جلد در این جابه‌جایی"
    )
    recipient_phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        db_index=True,
        verbose_name="شماره موبایل گیرنده (در صورت عدم عضویت یا ارسال پیامک)",
    )
    otp_code_hash = models.CharField(max_length=128, blank=True, default="", verbose_name="هش کد تایید موقت")
    otp_expires_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان انقضای کد تایید")

    donor_note = models.TextField(blank=True, default="", verbose_name="پیام یادگاری اهداکننده برای خواننده بعدی")
    recipient_note = models.TextField(blank=True, default="", verbose_name="بازخورد و پیام تشکر گیرنده")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان قطعی شدن انتقال")

    class Meta:
        db_table = "marketplace_book_transfers"
        verbose_name = "Book Transfer"
        verbose_name_plural = "Book Transfers"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(quantity__gte=1),
                name="chk_transfer_quantity_gte_1",
            )
        ]
        indexes = [
            models.Index(fields=["copy", "-created_at"], name="idx_trf_copy_created"),
            models.Index(fields=["from_user", "-created_at"], name="idx_trf_from_created"),
            models.Index(fields=["to_user", "-created_at"], name="idx_trf_to_created"),
            models.Index(fields=["recipient_phone", "status"], name="idx_trf_phone_status"),
            models.Index(fields=["status"], name="idx_trf_status"),
        ]

    def __str__(self):
        giver = self.from_user.get_full_name() if self.from_user else "قفسه تفاخر"
        receiver = self.to_user.get_full_name() if self.to_user else "قفسه تفاخر"
        return f"{self.copy.book_title.title}: {giver} -> {receiver} ({self.get_status_display()})"


class Badge(TimeStampedModel):
    """
    Gamification badge definitions (نشان‌های افتخار و ترویج مطالعه).
    """
    class Criteria(models.TextChoices):
        TRANSFERS_GIVEN = "transfers_given", "تعداد کتاب‌های اهداشده"
        TRANSFERS_RECEIVED = "transfers_received", "تعداد کتاب‌های دریافت‌شده"
        STATION_DEPOSITS = "station_deposits", "تعداد کتاب‌های گذاشته‌شده در قفسه‌ها"
        STREAK_DAYS = "streak_days", "تداوم مطالعه (روز متوالی)"

    slug = models.SlugField(max_length=50, unique=True, verbose_name="شناسه یکتا (slug)")
    title_fa = models.CharField(max_length=100, verbose_name="عنوان فارسی نشان")
    title_en = models.CharField(max_length=100, verbose_name="عنوان انگلیسی نشان")
    description_fa = models.TextField(blank=True, default="", verbose_name="شرح نحوه کسب نشان (فارسی)")
    description_en = models.TextField(blank=True, default="", verbose_name="شرح نحوه کسب نشان (انگلیسی)")
    icon = models.CharField(max_length=50, default="AwardIcon", verbose_name="نام آیکون لوساید")
    threshold = models.PositiveIntegerField(default=1, verbose_name="حد نصاب برای کسب نشان")
    criteria = models.CharField(
        max_length=30,
        choices=Criteria.choices,
        default=Criteria.TRANSFERS_GIVEN,
        verbose_name="معیار ارزیابی"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        db_table = "marketplace_badges"
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        ordering = ["order", "threshold"]

    def __str__(self):
        return f"{self.title_fa} ({self.threshold})"


class BadgeAward(TimeStampedModel):
    """
    Record of a badge earned by a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="earned_badges",
        verbose_name="کاربر"
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="awards",
        verbose_name="نشان کسب‌شده"
    )

    class Meta:
        db_table = "marketplace_badge_awards"
        verbose_name = "Badge Award"
        verbose_name_plural = "Badge Awards"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge_award")
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_badge_user_created"),
        ]

    def __str__(self):
        return f"{self.user} -> {self.badge.title_fa}"
