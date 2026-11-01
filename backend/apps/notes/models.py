import hashlib
import re
import uuid
from django.db import models
from django.utils import timezone
from apps.accounts.models import User, MessagingTarget


class Topic(models.Model):
    name = models.CharField(max_length=255)
    image = models.FileField(upload_to='topic_images/', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    post_badge = models.CharField(max_length=100, blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    POST_LINK_MODE_CHOICES = [
        ('auto_long', 'فقط پست‌های طولانی (خودکار)'),
        ('always', 'همیشه (حتی برای پست‌های کوتاه)'),
        ('disabled', 'غیرفعال'),
    ]

    # تنظیمات اتصال ربات‌ها
    telegram_bot_active = models.BooleanField(default=False)
    telegram_post_badge = models.CharField(max_length=100, blank=True, default='')
    telegram_post_link_mode = models.CharField(
        max_length=20,
        choices=POST_LINK_MODE_CHOICES,
        default='auto_long'
    )

    bale_bot_active = models.BooleanField(default=False)
    bale_post_badge = models.CharField(max_length=100, blank=True, default='')
    bale_post_link_mode = models.CharField(
        max_length=20,
        choices=POST_LINK_MODE_CHOICES,
        default='auto_long'
    )

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


def normalize_persian_text(text: str) -> str:
    """
    Normalizes Persian/Arabic characters and whitespace for accurate hash matching.
    """
    if not text:
        return ""

    replacements = {
        'ك': 'ک',
        'ي': 'ی',
        'ئ': 'ی',
        'إ': 'ا',
        'أ': 'ا',
        'آ': 'ا',
        '\u200c': ' ',  # Zero-Width Non-Joiner
    }

    text = text.strip().lower()
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r'\s+', ' ', text)
    return text


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

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # شناسه‌های پیام ارسال شده در پیام‌رسان‌ها (chat_id: message_id)
    telegram_message_ids = models.JSONField(default=dict, blank=True)
    bale_message_ids = models.JSONField(default=dict, blank=True)

    is_imported = models.BooleanField(default=False)
    telegram_message_id = models.IntegerField(null=True, blank=True)

    # Deduplication & Audit tracking fields
    content_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    published_platforms = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['created_at', 'telegram_message_id']
        indexes = [
            models.Index(fields=['topic', 'created_at']),
            models.Index(fields=['topic', 'content_hash']),
        ]

    def save(self, *args, **kwargs):
        if self.content or self.media_file:
            self.content_hash = self.compute_content_hash()
        super().save(*args, **kwargs)

    def compute_content_hash(self) -> str:
        hasher = hashlib.sha256()
        
        normalized_text = normalize_persian_text(self.content or "")
        hasher.update(normalized_text.encode('utf-8'))
        
        if self.media_file:
            try:
                if hasattr(self.media_file, 'size'):
                    hasher.update(str(self.media_file.size).encode('utf-8'))
            except (ValueError, FileNotFoundError):
                pass
                
        return hasher.hexdigest()

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    author_name = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        author_display = self.author_name if self.author_name else ("Anonymous" if self.is_anonymous else (self.user.phone if self.user else "Anonymous"))
        return f"Comment by {author_display} on Post {self.post.id}"


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


class TopicFAQ(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='faqs'
    )
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_faqs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['topic', 'order']),
            models.Index(fields=['topic', 'is_published']),
        ]

    def __str__(self):
        return f"FAQ: {self.question[:50]} ({self.topic.name})"


class TopicChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='topic_chat_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        user_display = self.user.phone if self.user else "Anonymous"
        return f"ChatSession {self.id} ({self.topic.name}) by {user_display}"


class TopicChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        TopicChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}"


class PostEditProposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    editor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='editor_proposals'
    )
    original_content = models.TextField()
    proposed_content = models.TextField()
    reason = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_proposals'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Proposal {self.id} for Post {self.post_id} by {self.editor.phone} ({self.status})"


class PostEditHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='edit_history'
    )
    proposal = models.ForeignKey(
        PostEditProposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_records'
    )
    editor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applied_edits'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_edits'
    )
    previous_content = models.TextField()
    new_content = models.TextField()
    summary_of_changes = models.CharField(max_length=500, blank=True, default='')
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['post', '-applied_at']),
        ]

    def __str__(self):
        return f"History {self.id} on Post {self.post_id} at {self.applied_at}"

