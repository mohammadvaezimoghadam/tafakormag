import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class DonationCampaign(models.Model):
    class CategoryChoices(models.TextChoices):
        # Frontend UI Categories
        MOSQUE = 'mosque', 'مسجد و اماکن مذهبی'
        SCHOOL = 'school', 'مدرسه و آموزش'
        HEALTH = 'health', 'درمانی و سلامت'
        LIVELIHOOD = 'livelihood', 'نیازمندان و معیشت'
        CONSTRUCTION = 'construction', 'عمرانی و تجهیزات'
        OTHER = 'other', 'متفرقه و عمومی'

        # Extended Category Aliases
        TREATMENT = 'treatment', 'درمانی و سلامت'
        EDUCATION = 'education', 'آموزش و تحصیلی'
        LIVING = 'living', 'معیشتی و نیازمندان'
        FREEDOM = 'freedom', 'آزادی زندانیان'
        DOWRY = 'dowry', 'جهیزیه'
        EMPLOYMENT = 'employment', 'اشتغال و کارآفرینی'
        GENERAL = 'general', 'عمومی و متفرقه'

    class StatusChoices(models.TextChoices):
        PENDING_REVIEW = 'pending_review', 'در انتظار تأیید'
        ACTIVE = 'active', 'در حال جمع‌آوری'
        COMPLETED = 'completed', 'تکمیل‌شده'
        EXPIRED = 'expired', 'منقضی‌شده'
        PAUSED = 'paused', 'متوقف/در حال بررسی'
        INACTIVE = 'inactive', 'متوقف و غیرفعال‌شده'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey('notes.Topic', on_delete=models.CASCADE, related_name='donation_campaigns')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_campaigns')
    post = models.OneToOneField('notes.Post', null=True, blank=True, on_delete=models.SET_NULL, related_name='donation_campaign')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CategoryChoices.choices, default=CategoryChoices.GENERAL)
    
    target_amount = models.BigIntegerField(validators=[MinValueValidator(100000)])  # Minimum 100,000 Tomans
    collected_amount = models.BigIntegerField(default=0)
    donors_count = models.PositiveIntegerField(default=0)
    
    cover_image = models.FileField(upload_to='donations/covers/', null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    iban = models.CharField(max_length=34, null=True, blank=True)
    is_public_donors_list = models.BooleanField(default=True)
    
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'donation_campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['topic', 'status']),
            models.Index(fields=['category']),
        ]

    def clean(self):
        super().clean()
        if self.target_amount is not None and self.target_amount < 100000:
            raise ValidationError({'target_amount': 'حداقل مبلغ هدف پویش ۱۰۰,۰۰۰ تومان است.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def check_and_update_status(self):
        """
        Auto-evaluates whether campaign is completed (including overfunding) or expired.
        """
        if self.status == self.StatusChoices.ACTIVE:
            if self.collected_amount >= self.target_amount:
                self.status = self.StatusChoices.COMPLETED
                self.save(update_fields=['status', 'updated_at'])
            elif self.deadline and timezone.now() > self.deadline:
                self.status = self.StatusChoices.EXPIRED
                self.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def total_settled_amount(self) -> int:
        from django.db.models import Sum
        total = self.payout_requests.filter(status='completed').aggregate(Sum('amount'))['amount__sum']
        return total or 0

    @property
    def available_payout_balance(self) -> int:
        return max(0, self.collected_amount - self.total_settled_amount)

    @property
    def is_ended(self) -> bool:
        """Campaign is ended when status is terminal, deadline has passed, or target amount is reached."""
        if self.status in [self.StatusChoices.COMPLETED, self.StatusChoices.EXPIRED, self.StatusChoices.INACTIVE]:
            return True
        if self.deadline and self.deadline < timezone.now():
            return True
        if self.target_amount > 0 and self.collected_amount >= self.target_amount:
            return True
        return False


class CampaignAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='donations/attachments/')
    is_video = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'donation_campaign_attachments'
        ordering = ['created_at']

    def __str__(self):
        return f"Attachment {self.id} for {self.campaign_id}"


class DonationTransaction(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        SUCCESSFUL = 'successful', 'موفق'
        FAILED = 'failed', 'ناموفق'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.CASCADE, related_name='transactions')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    payment_transaction = models.OneToOneField(
        'payments.PaymentTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donation_transaction',
    )
    
    amount = models.BigIntegerField(validators=[MinValueValidator(1000)])  # Minimum 1,000 Tomans
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    authority = models.CharField(max_length=100, unique=True, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, null=True, blank=True)
    gateway_reference_id = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'donation_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['authority']),
        ]

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount < 1000:
            raise ValidationError({'amount': 'حداقل مبلغ واریزی ۱,۰۰۰ تومان است.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Trx {self.authority or self.id} - {self.amount} Tomans ({self.status})"


class TransparencyLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.CASCADE, related_name='transparency_logs')
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    amount = models.BigIntegerField()
    receipt_image = models.FileField(upload_to='donations/receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'donation_transparency_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transparency: {self.title} ({self.amount} Tomans)"


class PayoutRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار بررسی'
        APPROVED = 'approved', 'تأییدشده / در نوبت پرداخت'
        COMPLETED = 'completed', 'واریزشده و تسویه‌شده'
        REJECTED = 'rejected', 'ردشده'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.CASCADE,
        related_name='payout_requests',
        verbose_name='پویش مرتبط'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='donation_payout_requests',
        verbose_name='درخواست‌دهنده'
    )
    amount = models.BigIntegerField(
        validators=[MinValueValidator(10000)],
        verbose_name='مبلغ درخواستی (تومان)'
    )
    iban = models.CharField(
        max_length=34,
        verbose_name='شماره شبا'
    )
    account_holder_name = models.CharField(
        max_length=150,
        verbose_name='نام صاحب حساب'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='وضعیت تسویه'
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='شماره پیگیری فیش بانکی (پایا/ساتنا)'
    )
    receipt_file = models.FileField(
        upload_to='donations/payouts/',
        null=True,
        blank=True,
        verbose_name='تصویر فیش واریز'
    )
    rejection_reason = models.TextField(
        blank=True,
        default='',
        verbose_name='علت رد درخواست'
    )
    admin_notes = models.TextField(
        blank=True,
        default='',
        verbose_name='یادداشت مدیر'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='processed_donation_payouts',
        verbose_name='بررسی‌کننده'
    )
    settled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان واریز نهایی'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت درخواست')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        db_table = 'donation_payout_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Payout {self.id} | {self.amount:,} تومان ({self.get_status_display()})"

