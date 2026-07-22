from django.db import models
from django.utils import timezone
from apps.accounts.models import User, MessagingTarget
import uuid


class Topic(models.Model):
    name = models.CharField(max_length=255)
    image = models.FileField(upload_to='topic_images/', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # تنظیمات اتصال ربات‌ها
    telegram_bot_active = models.BooleanField(default=False)
    bale_bot_active = models.BooleanField(default=False)

    telegram_connections = models.ManyToManyField(
        MessagingTarget,
        related_name="telegram_topics",
        blank=True
    )
    bale_connections = models.ManyToManyField(
        MessagingTarget,
        related_name="bale_topics",
        blank=True
    )

    def __str__(self):
        return self.name


class Post(models.Model):
    MEDIA_CHOICES = [
        ("text", "text"),
        ("image", "image"),
        ("video", "video"),
        ("audio", "audio"),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True, default="")  # Markdown text
    
    media_type = models.CharField(max_length=20, choices=MEDIA_CHOICES, default="text")
    media_file = models.FileField(upload_to='post_media/', null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # شناسه‌های پیام ارسال شده در پیام‌رسان‌ها (chat_id: message_id)
    telegram_message_ids = models.JSONField(default=dict, blank=True)
    bale_message_ids = models.JSONField(default=dict, blank=True)

    is_imported = models.BooleanField(default=False)
    telegram_message_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['created_at', 'telegram_message_id']

    def __str__(self):
        return f"Post by {self.author.phone} in {self.topic.name} at {self.created_at}"


class PostReaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  # 👍, 👎, ❤️, 😂, 🎉
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.phone} reacted {self.emoji} on Post {self.post.id}"


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.phone} on Post {self.post.id}"


class BotTask(models.Model):
    ACTION_CHOICES = [
        ("send", "send"),
        ("edit", "edit"),
        ("delete", "delete"),
    ]
    PLATFORM_CHOICES = [
        ("telegram", "telegram"),
        ("bale", "bale"),
    ]

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    chat_id = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    message_id = models.CharField(max_length=100, null=True, blank=True)
    note_id = models.BigIntegerField(null=True, blank=True) # برای سازگاری با کدهای قدیمی
    post_id = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='bot_tasks')
    bot_token = models.CharField(max_length=255, null=True, blank=True)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["processed", "created_at"]),
        ]

    def __str__(self):
        return f"BotTask({self.action}, {self.platform}, processed={self.processed})"


class ImportTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('EXTRACTING', 'Extracting'),
        ('IMPORTING', 'Importing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='import_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    current_stage = models.CharField(max_length=255, default='Pending')
    progress = models.IntegerField(default=0)  # 0 to 100
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ImportTask {self.id} ({self.status})"


class TopicAdmin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='admins'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='administered_topics'
    )
    promoted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promoted_admins'
    )
    custom_title = models.CharField(max_length=50, default='Admin', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('topic', 'user')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.phone} - Admin of {self.topic.name}"