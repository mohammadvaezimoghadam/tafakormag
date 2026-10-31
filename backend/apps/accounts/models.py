# note_platform/apps/accounts/models.py
import uuid
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        if not phone:
            raise ValueError('شماره موبایل الزامی است')
        user = self.model(phone=phone)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, phone, password):
        user = self.create_user(phone, password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user
    
class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=11, unique=True)
    is_active = models.BooleanField(default=True)

    # فیلدهای دسترسی را صریحاً اضافه می‌کنیم (PermissionsMixin هم هست ولی برای اطمینان)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_image = models.FileField(upload_to='profile_images/', null=True, blank=True)

    telegram_chat_id = models.CharField(max_length=100, null=True, blank=True)
    bale_chat_id = models.CharField(max_length=100, null=True, blank=True)

    telegram_bot_token = models.CharField(max_length=255, null=True, blank=True)
    telegram_bot_username = models.CharField(max_length=255, null=True, blank=True)
    telegram_bot_disconnect_reason = models.CharField(max_length=255, null=True, blank=True)
    bale_bot_token = models.CharField(max_length=255, null=True, blank=True)
    bale_bot_username = models.CharField(max_length=255, null=True, blank=True)
    bale_bot_disconnect_reason = models.CharField(max_length=255, null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.phone

    def get_short_name(self):
        return self.first_name or self.phone

    # برای سازگاری با PermissionsMixin، متدهای زیر باید باشند (اگر نباشند)
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

class BotConnectionToken(models.Model):
    PLATFORM_CHOICES = [
        ("bale", "بله"),
        ("telegram", "تلگرام"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)


    def is_valid(self):
        delta = timezone.now() - self.created_at
        return delta.total_seconds() < 600 and not self.is_used


class MessagingTarget(models.Model):
    PLATFORM_CHOICES = [
        ("telegram", "Telegram"),
        ("bale", "Bale"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messaging_targets"
    )
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    chat_id = models.CharField(max_length=100)
    label = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "platform", "chat_id"],
                name="unique_user_platform_chat",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.is_default:
            MessagingTarget.objects.filter(
                user=self.user,
                platform=self.platform,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label} ({self.platform}, {self.chat_id})"