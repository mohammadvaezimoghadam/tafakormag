from django.contrib import admin
from .models import DonationCampaign, DonationTransaction, TransparencyLog, CampaignAttachment


class CampaignAttachmentInline(admin.TabularInline):
    model = CampaignAttachment
    extra = 1


class TransparencyLogInline(admin.StackedInline):
    model = TransparencyLog
    extra = 1


class DonationTransactionInline(admin.TabularInline):
    model = DonationTransaction
    extra = 0
    readonly_fields = ['id', 'donor', 'amount', 'is_anonymous', 'status', 'authority', 'tracking_code', 'completed_at']
    can_delete = False


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'creator', 'category', 'target_amount', 'collected_amount', 'donors_count', 'status', 'created_at']
    list_filter = ['status', 'category', 'is_public_donors_list', 'created_at']
    search_fields = ['title', 'description', 'creator__username', 'creator__email']
    readonly_fields = ['id', 'collected_amount', 'donors_count', 'created_at', 'updated_at']
    inlines = [CampaignAttachmentInline, TransparencyLogInline, DonationTransactionInline]


@admin.register(DonationTransaction)
class DonationTransactionAdmin(admin.ModelAdmin):
    list_display = ['authority', 'campaign', 'donor', 'amount', 'is_anonymous', 'status', 'tracking_code', 'completed_at']
    list_filter = ['status', 'is_anonymous', 'created_at']
    search_fields = ['authority', 'tracking_code', 'gateway_reference_id', 'donor__username']
    readonly_fields = ['id', 'created_at', 'completed_at']


@admin.register(TransparencyLog)
class TransparencyLogAdmin(admin.ModelAdmin):
    list_display = ['title', 'campaign', 'amount', 'created_at']
    search_fields = ['title', 'description', 'campaign__title']
    readonly_fields = ['id', 'created_at']


@admin.register(CampaignAttachment)
class CampaignAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'campaign', 'is_video', 'created_at']
