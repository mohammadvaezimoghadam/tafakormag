from django.contrib import admin
from .models import DonationCampaign, DonationTransaction, TransparencyLog, CampaignAttachment, PayoutRequest


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


class PayoutRequestInline(admin.TabularInline):
    model = PayoutRequest
    extra = 0
    readonly_fields = ['id', 'requested_by', 'amount', 'iban', 'account_holder_name', 'status', 'tracking_number', 'settled_at', 'created_at']
    can_delete = False


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'creator', 'category', 'target_amount', 'collected_amount', 'donors_count', 'status', 'created_at']
    list_filter = ['status', 'category', 'is_public_donors_list', 'created_at']
    search_fields = ['title', 'description', 'creator__username', 'creator__email']
    readonly_fields = ['id', 'collected_amount', 'donors_count', 'created_at', 'updated_at']
    actions = ['approve_campaigns']
    inlines = [CampaignAttachmentInline, TransparencyLogInline, DonationTransactionInline, PayoutRequestInline]

    @admin.action(description='تأیید پویش‌های انتخاب‌شده (تغییر وضعیت به فعال)')
    def approve_campaigns(self, request, queryset):
        from django.db import transaction
        from apps.notes.models import Post

        pending = queryset.filter(status=DonationCampaign.StatusChoices.PENDING_REVIEW)
        count = 0
        with transaction.atomic():
            for campaign in pending:
                campaign.status = DonationCampaign.StatusChoices.ACTIVE
                if not campaign.post:
                    post_content = f"🤲 **پویش مهربانی: {campaign.title}**\n\n{campaign.description}\n\n🎯 مبلغ هدف: {campaign.target_amount:,} تومان"
                    post = Post.objects.create(
                        topic=campaign.topic,
                        author=campaign.creator,
                        content=post_content,
                        media_type="image" if campaign.cover_image else "text",
                        media_file=campaign.cover_image.name if campaign.cover_image else None
                    )
                    campaign.post = post
                    campaign.save(update_fields=['status', 'post', 'updated_at'])
                else:
                    campaign.save(update_fields=['status', 'updated_at'])
                count += 1

        self.message_user(request, f'{count} پویش با موفقیت تأیید و فعال شد.')


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


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'campaign', 'amount', 'account_holder_name', 'iban',
        'status', 'tracking_number', 'settled_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'settled_at']
    search_fields = [
        'campaign__title', 'account_holder_name', 'iban',
        'tracking_number', 'requested_by__phone'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_select_related = ['campaign', 'requested_by', 'processed_by']

