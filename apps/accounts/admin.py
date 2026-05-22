from django import forms
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import MessagingTarget, User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone',)

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('phone', 'is_active', 'is_staff', 'is_superuser', 'telegram_chat_id', 'bale_chat_id')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('phone',)
    ordering = ('phone',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('اطلاعات پیام‌رسان‌ها', {'fields': ('telegram_chat_id', 'bale_chat_id')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌های مهم', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('phone', 'password1', 'password2')}),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


@admin.register(MessagingTarget)
class MessagingTargetAdmin(admin.ModelAdmin):
    list_display = ("label", "user", "platform", "chat_id", "is_default", "created_at")
    list_filter = ("platform", "is_default")
    search_fields = ("label", "chat_id", "user__phone")
    raw_id_fields = ("user",)