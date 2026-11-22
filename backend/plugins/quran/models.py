import secrets
import string
from django.conf import settings
from django.db import models


class QuranEdition(models.Model):
    """
    Represents a specific Quran edition, translation, transliteration, or audio recitation.
    """
    TYPE_CHOICES = [
        ('quran', 'Original Quran Text'),
        ('translation', 'Translation'),
        ('transliteration', 'Transliteration'),
        ('tafsir', 'Tafsir / Commentary'),
        ('audio', 'Audio Recitation'),
    ]
    FORMAT_CHOICES = [
        ('text', 'Text'),
        ('audio', 'Audio'),
    ]
    DIRECTION_CHOICES = [
        ('rtl', 'Right-to-Left (RTL)'),
        ('ltr', 'Left-to-Right (LTR)'),
    ]

    identifier = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique slug (e.g. 'quran-simple', 'fa.ansarian', 'en.sahih')"
    )
    name = models.CharField(max_length=150, help_text="Localized name (e.g. 'ترجمه انصاریان')")
    english_name = models.CharField(max_length=150, help_text="English name (e.g. 'Ansarian Translation')")
    language = models.CharField(max_length=10, db_index=True, help_text="ISO 639-1 code ('ar', 'fa', 'en', etc.)")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='translation', db_index=True)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='text')
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES, default='rtl')
    author = models.CharField(max_length=150, blank=True, default='')
    is_default = models.BooleanField(default=False, db_index=True, help_text="Default edition for language/type")
    total_ayahs = models.IntegerField(default=6236)
    metadata = models.JSONField(default=dict, blank=True, help_text="Source url, license, audio bitrate, reciter details")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quran_editions'
        ordering = ['language', 'type', 'name']
        verbose_name = 'Quran Edition'
        verbose_name_plural = 'Quran Editions'

    def __str__(self):
        return f"{self.name} ({self.identifier})"


class QuranSurah(models.Model):
    """
    Represents the canonical 114 Surahs (chapters) of the Holy Quran.
    """
    REVELATION_CHOICES = [
        ('Meccan', 'Meccan (مکی)'),
        ('Medinan', 'Medinan (مدنی)'),
    ]

    number = models.IntegerField(primary_key=True, help_text="Surah Number (1 to 114)")
    name = models.CharField(max_length=100, help_text="Arabic name (e.g. 'الفاتحة')")
    english_name = models.CharField(max_length=100, help_text="Transliterated name (e.g. 'Al-Faatiha')")
    english_name_translation = models.CharField(max_length=150, help_text="English translation (e.g. 'The Opening')")
    revelation_type = models.CharField(max_length=20, choices=REVELATION_CHOICES, db_index=True)
    ayah_count = models.IntegerField(help_text="Total number of Ayahs in this Surah")
    order_of_revelation = models.IntegerField(null=True, blank=True)
    page_start = models.IntegerField(null=True, blank=True, help_text="Starting page in standard 604-page Madinah Mushaf")
    page_end = models.IntegerField(null=True, blank=True)
    juz_start = models.IntegerField(default=1)
    bismillah_pre = models.BooleanField(
        default=True,
        help_text="True if Bismillah is displayed before Surah (False for Surah At-Tawbah #9)"
    )

    class Meta:
        db_table = 'quran_surahs'
        ordering = ['number']
        verbose_name = 'Quran Surah'
        verbose_name_plural = 'Quran Surahs'

    def __str__(self):
        return f"{self.number}. {self.name} ({self.english_name})"


class QuranJuz(models.Model):
    """
    Represents the 30 Juzs (parts) of the Quran and their Surah boundary mappings.
    """
    number = models.IntegerField(primary_key=True, help_text="Juz Number (1 to 30)")
    name = models.CharField(max_length=100, blank=True, default='', help_text="e.g. 'جزء ۱', 'جزء ۳۰ (عمّ)'")
    start_surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='juz_starts')
    start_ayah = models.IntegerField(help_text="Ayah number in start surah")
    end_surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='juz_ends')
    end_ayah = models.IntegerField(help_text="Ayah number in end surah")
    surah_mapping = models.JSONField(
        default=list,
        blank=True,
        help_text="List of surah segments: [{'surah': 1, 'ayah_from': 1, 'ayah_to': 7}, ...]"
    )

    class Meta:
        db_table = 'quran_juzs'
        ordering = ['number']
        verbose_name = 'Quran Juz'
        verbose_name_plural = 'Quran Juzs'

    def __str__(self):
        return f"Juz {self.number} ({self.name or self.number})"


class QuranAyah(models.Model):
    """
    Represents an individual Ayah (verse) for a specific Edition.
    """
    id = models.BigAutoField(primary_key=True)
    edition = models.ForeignKey(QuranEdition, on_delete=models.CASCADE, related_name='ayahs', db_index=True)
    surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name='ayahs', db_index=True)
    number = models.IntegerField(db_index=True, help_text="Global Ayah number across the Quran (1 to 6236)")
    number_in_surah = models.IntegerField(db_index=True, help_text="Ayah number within the Surah (1 to surah.ayah_count)")
    juz = models.IntegerField(db_index=True, help_text="Juz number (1 to 30)")
    manzil = models.IntegerField(null=True, blank=True, help_text="Manzil (1 to 7)")
    page = models.IntegerField(null=True, blank=True, db_index=True, help_text="Standard Madinah Mushaf page (1 to 604)")
    ruku = models.IntegerField(null=True, blank=True)
    hizb_quarter = models.IntegerField(null=True, blank=True, help_text="Hizb quarter (1 to 240)")
    sajda = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Sajda details (e.g. {'recommended': true, 'obligatory': false} or null)"
    )
    text = models.TextField(help_text="Authentic original text with full diacritics / Uthmani script / translation")
    normalized_text = models.TextField(
        blank=True,
        db_index=True,
        help_text="Diacritic-stripped and standardized text for fast search indexing"
    )
    audio_url = models.URLField(max_length=500, blank=True, null=True, help_text="Ayah-specific audio stream URL")
    metadata = models.JSONField(default=dict, blank=True, help_text="Footnotes, audio offsets, word-by-word data")

    class Meta:
        db_table = 'quran_ayahs'
        ordering = ['surah', 'number_in_surah']
        constraints = [
            models.UniqueConstraint(
                fields=['edition', 'number'],
                name='unique_edition_global_number'
            ),
            models.UniqueConstraint(
                fields=['edition', 'surah', 'number_in_surah'],
                name='unique_edition_surah_ayah'
            )
        ]
        indexes = [
            models.Index(fields=['edition', 'surah', 'number_in_surah']),
            models.Index(fields=['edition', 'juz']),
            models.Index(fields=['edition', 'page']),
            models.Index(fields=['surah', 'number_in_surah']),
            models.Index(fields=['edition', 'normalized_text']),
        ]
        verbose_name = 'Quran Ayah'
        verbose_name_plural = 'Quran Ayahs'

    def __str__(self):
        return f"{self.edition_id} | {self.surah.name}:{self.number_in_surah}"


# ==============================================================================
# Group Khatm (Collaborative Quran Reading) Models
# ==============================================================================

def generate_khatm_invite_code(length=8):
    """
    Generates a secure, human-friendly, alphanumeric invite code for campaign sharing.
    Example output: 'X7k9P2mQ'
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class KhatmCategory(models.Model):
    """
    Represents an intention or category for a Khatm (e.g., deceased, healing, Ramadan, martyrs).
    """
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100, help_text="عنوان دسته (مثل: درگذشتگان، سلامتی و فرج)")
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, help_text="شناسه انگلیسی یا یکتا برای فیلتر")
    icon = models.CharField(max_length=50, blank=True, default='', help_text="نام آیکون در فلاتر یا ایموجی")
    display_order = models.PositiveIntegerField(default=0, help_text="ترتیب نمایش در اپ")
    is_active = models.BooleanField(default=True, db_index=True, help_text="آیا فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'khatm_categories'
        ordering = ['display_order', 'id']
        verbose_name = 'Khatm Category'
        verbose_name_plural = 'Khatm Categories'

    def __str__(self):
        return self.title


class KhatmCampaign(models.Model):
    """
    Represents a collective Quran Khatm Campaign.
    """
    class UnitType(models.TextChoices):
        JUZ = 'juz', 'جزء'
        HIZB = 'hizb', 'حزب'
        SURAH = 'surah', 'سوره'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'فعال'
        COMPLETED = 'completed', 'تکمیل شده'
        EXPIRED = 'expired', 'منقضی شده'

    id = models.BigAutoField(primary_key=True)
    invite_code = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        default=generate_khatm_invite_code,
        help_text="کد کوتاه یکتا برای لینک دعوت و API"
    )
    category = models.ForeignKey(
        KhatmCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        help_text="دسته نیت مربوطه"
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_khatms',
        help_text="کاربر سازنده ختم"
    )
    title = models.CharField(max_length=200, help_text="عنوان ختم مثلا: ختم سوره یس برای اموات")
    description = models.TextField(blank=True, default='', help_text="متن توضیحات و نیت یا هدیه ثواب")

    unit_type = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.JUZ,
        db_index=True,
        help_text="واحد تقسیم: جزء، حزب، یا سوره"
    )
    target_units = models.PositiveIntegerField(
        help_text="تعداد کل واحدها (۳۰ برای جزء، ۱۲۰ برای حزب، یا تعداد کل سوره)"
    )
    target_surah = models.ForeignKey(
        QuranSurah,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='khatm_campaigns',
        help_text="شماره سوره در صورتی که واحد سوره باشد"
    )

    reserved_units = models.PositiveIntegerField(
        default=0,
        help_text="تعداد واحدهای رزرو شده (برای سرعت بالای نوار پیشرفت)"
    )
    completed_units = models.PositiveIntegerField(
        default=0,
        help_text="تعداد واحدهای قرائت شده (برای سرعت بالای نوار پیشرفت)"
    )

    is_public = models.BooleanField(
        default=True,
        db_index=True,
        help_text="نمایش در ویترین عمومی برنامه"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="وضعیت پویش"
    )

    deadline = models.DateTimeField(null=True, blank=True, help_text="مهلت زمانی تعیین شده")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="حذف نرم برای حفظ سوابق قرائت")

    class Meta:
        db_table = 'khatm_campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['category', 'created_at'],
                condition=models.Q(is_public=True, status='active', deleted_at__isnull=True),
                name='idx_campaigns_feed',
            ),
            models.Index(fields=['creator', 'status'], name='idx_campaigns_creator'),
        ]
        verbose_name = 'Khatm Campaign'
        verbose_name_plural = 'Khatm Campaigns'

    def __str__(self):
        return f"{self.title} ({self.invite_code})"


class KhatmSlot(models.Model):
    """
    Represents an allocated portion/slot within a Khatm Campaign.
    """
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'آزاد'
        RESERVED = 'reserved', 'در حال قرائت'
        COMPLETED = 'completed', 'قرائت شده'

    id = models.BigAutoField(primary_key=True)
    campaign = models.ForeignKey(
        KhatmCampaign,
        on_delete=models.CASCADE,
        related_name='slots',
        help_text="پویش مربوطه"
    )
    unit_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="شماره جزء یا حزب (برای ختم سوره null است)"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="تعداد سهم (برای جزء و حزب ۱، برای سوره تعداد دلخواه کاربر)"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='khatm_slots',
        help_text="کاربری که سهم را برداشته است"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
        help_text="وضعیت سهم"
    )
    reserved_at = models.DateTimeField(null=True, blank=True, help_text="زمان رزرو سهم")
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="زمان انقضای رزرو برای آزادسازی خودکار")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="زمان اعلام اتمام قرائت")

    class Meta:
        db_table = 'khatm_slots'
        constraints = [
            models.UniqueConstraint(
                fields=['campaign', 'unit_number'],
                condition=models.Q(unit_number__isnull=False),
                name='unique_campaign_unit_number'
            )
        ]
        indexes = [
            models.Index(fields=['campaign', 'status'], name='idx_slots_campaign_status'),
            models.Index(fields=['user', 'status'], name='idx_slots_user_status'),
            models.Index(fields=['status', 'expires_at'], name='idx_slots_expiration'),
        ]
        verbose_name = 'Khatm Slot'
        verbose_name_plural = 'Khatm Slots'

    def __str__(self):
        unit_str = f"Unit {self.unit_number}" if self.unit_number else f"Qty {self.quantity}"
        return f"{self.campaign.invite_code} - {unit_str} ({self.status})"


class PersonalKhatmPlan(models.Model):
    """
    Represents a synchronized Personal Khatm / Reading Plan of a user (Offline-First sync).
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='personal_khatm_plans',
        help_text="کاربر صاحب ختم"
    )
    client_id = models.CharField(
        max_length=36,
        help_text="شناسه یکتای UUID تولید شده در فلاتر برای سینک آفلاین"
    )
    title = models.CharField(max_length=200, help_text="عنوان ختم فردی")
    unit_type = models.CharField(max_length=20, help_text="واحد: page, hizb, juz, surah, ayah")
    range_from = models.PositiveIntegerField(default=1)
    range_to = models.PositiveIntegerField()

    planning_mode = models.CharField(max_length=30, help_text="bySessionCount یا byUnitQuota")
    session_count = models.PositiveIntegerField()
    quota_per_session = models.PositiveIntegerField()
    cadence = models.CharField(max_length=30, help_text="daily, everyOtherDay, weekly, customWeekdays")
    selected_weekdays = models.JSONField(default=list, blank=True, help_text="آرایه روزهای انتخابی مثلا [6, 1, 3]")

    start_date = models.DateField()
    end_date = models.DateField()

    sessions_progress = models.JSONField(
        default=list,
        blank=True,
        help_text="لیست پیشرفت جلسات (سریالایز مستقیم از KhatmSessionItem در فلاتر)"
    )
    completed_sessions = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    client_updated_at = models.DateTimeField(help_text="زمان آخرین تغییر در گوشی برای حل تداخل (Last-Write-Wins)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="حذف نرم برای همگام‌سازی حذف‌ها بین دستگاه‌ها")

    class Meta:
        db_table = 'personal_khatm_plans'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'client_id'],
                name='unique_user_client_khatm'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'is_archived', 'deleted_at'], name='idx_personal_khatm_user'),
        ]
        verbose_name = 'Personal Khatm Plan'
        verbose_name_plural = 'Personal Khatm Plans'

    def __str__(self):
        return f"{self.user} - {self.title} ({self.client_id})"


