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
