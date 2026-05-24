from django.db import models
from apps.accounts.models import User



class Channel(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=100, unique=True)
    bale_chat_id = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name
    

    def delete(self, *args, **kwargs):
        if self.notes.exists():
            raise models.ProtectedError("این کانال یاداشت هایی دارد و نمیتوان آن را حذف کرد",self)
        
        super().delete(*args, **kwargs)



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
    note_id = models.BigIntegerField(null=True, blank=True)
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


class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes')
    title = models.CharField(max_length=500, blank=True, null=True)
    content = models.TextField()       # Markdown
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # انتخاب‌های کاربر هنگام ذخیره (boolean)
    send_to_telegram = models.BooleanField(default=False)
    send_to_bale = models.BooleanField(default=False)

    # شناسه‌های پیام اگر ارسال شده باشد
    telegram_message_id = models.CharField(max_length=100, null=True, blank=True)
    bale_message_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']



        