from django.contrib import admin
from .models import KhatmCategory, KhatmCampaign, KhatmSlot, PersonalKhatmPlan


class KhatmSlotInline(admin.TabularInline):
    model = KhatmSlot
    extra = 0
    fields = ('unit_number', 'quantity', 'user', 'status', 'reserved_at', 'expires_at', 'completed_at')
    readonly_fields = ('reserved_at', 'completed_at')
    raw_id_fields = ('user',)  # Prevents rendering thousands of users in dropdowns


@admin.register(KhatmCategory)
class KhatmCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'display_order', 'is_active', 'created_at')
    list_editable = ('display_order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'slug')


@admin.register(KhatmCampaign)
class KhatmCampaignAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'invite_code',
        'category',
        'unit_type',
        'target_units',
        'reserved_units',
        'completed_units',
        'status',
        'is_public',
        'created_at',
    )
    list_filter = ('unit_type', 'status', 'is_public', 'category')
    search_fields = ('title', 'invite_code', 'creator__mobile')
    raw_id_fields = ('creator', 'target_surah')  # Fast lookup without massive query
    inlines = [KhatmSlotInline]


@admin.register(PersonalKhatmPlan)
class PersonalKhatmPlanAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'unit_type',
        'session_count',
        'completed_sessions',
        'is_completed',
        'is_archived',
        'client_updated_at',
    )
    list_filter = ('unit_type', 'is_completed', 'is_archived')
    search_fields = ('title', 'user__mobile', 'client_id')
    raw_id_fields = ('user',)  # Prevents browser freezing on large user tables
