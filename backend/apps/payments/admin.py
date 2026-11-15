from django.contrib import admin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Django Admin configuration for centralized payment transactions and audit logs."""

    list_display = [
        "id",
        "purpose",
        "reference_id",
        "user",
        "amount",
        "gateway",
        "status",
        "authority",
        "ref_id",
        "created_at",
    ]
    list_filter = ["purpose", "gateway", "status", "created_at"]
    search_fields = ["id", "authority", "ref_id", "tracking_code", "reference_id", "user__phone"]
    list_select_related = ["user"]
    readonly_fields = [
        "id",
        "raw_request",
        "raw_verify_response",
        "verified_at",
        "settled_at",
        "created_at",
        "updated_at",
    ]

