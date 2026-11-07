from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import SubscriptionPlan, UserSubscription, PurchaseVerificationLog


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'plugin_identifier', 'sku', 'duration_days', 'price', 'is_active', 'updated_at')
    list_filter = ('plugin_identifier', 'is_active')
    search_fields = ('title', 'sku', 'description')
    ordering = ('plugin_identifier', 'duration_days')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plugin_identifier', 'plan', 'realtime_status_display', 'starts_at', 'expires_at', 'source', 'is_valid_display')
    list_filter = ('plugin_identifier', 'status', 'source')
    search_fields = ('user__phone', 'user__first_name', 'user__last_name', 'plugin_identifier')
    raw_id_fields = ('user', 'plan')
    date_hierarchy = 'expires_at'

    def get_queryset(self, request):
        # به‌روزرسانی خودکار وضعیت رکوردهای منقضی‌شده در دیتابیس
        UserSubscription.objects.filter(
            status='active',
            expires_at__lte=timezone.now()
        ).update(status='expired')
        return super().get_queryset(request)

    @admin.display(description='وضعیت لحظه‌ای')
    def realtime_status_display(self, obj):
        if obj.is_currently_valid:
            diff = obj.expires_at - timezone.now()
            mins = int(diff.total_seconds() // 60)
            if mins > 60:
                hours = mins // 60
                return format_html('<span style="color: #27ae60; font-weight: bold;">فعال ({} ساعت مانده)</span>', hours)
            return format_html('<span style="color: #27ae60; font-weight: bold;">فعال ({} دقیقه مانده)</span>', max(1, mins))
        return format_html('<span style="color: #c0392b; font-weight: bold;">منقضی‌شده</span>')

    @admin.display(boolean=True, description='دسترسی معتبر')
    def is_valid_display(self, obj):
        return obj.is_currently_valid


@admin.register(PurchaseVerificationLog)
class PurchaseVerificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sku', 'marketplace', 'is_verified', 'purchase_token_preview', 'created_at')
    list_filter = ('marketplace', 'is_verified', 'created_at')
    search_fields = ('user__phone', 'user__first_name', 'user__last_name', 'sku', 'purchase_token')
    raw_id_fields = ('user', 'plan')
    readonly_fields = ('created_at', 'bazaar_payload')

    def purchase_token_preview(self, obj):
        return f"{obj.purchase_token[:15]}..." if obj.purchase_token and len(obj.purchase_token) > 15 else obj.purchase_token
    purchase_token_preview.short_description = 'توکن خرید'
