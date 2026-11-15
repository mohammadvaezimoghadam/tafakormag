from rest_framework import serializers
from .models import PaymentTransaction


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Read serializer exposing safe audit & receipt fields for a centralized payment."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    gateway_display = serializers.CharField(source="get_gateway_display", read_only=True)
    purpose_display = serializers.CharField(source="get_purpose_display", read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "purpose",
            "purpose_display",
            "reference_id",
            "amount",
            "currency",
            "gateway",
            "gateway_display",
            "authority",
            "ref_id",
            "tracking_code",
            "card_pan",
            "fee",
            "status",
            "status_display",
            "description",
            "verified_at",
            "settled_at",
            "created_at",
        ]
        read_only_fields = fields


class PaymentVerifyInputSerializer(serializers.Serializer):
    """Input validator for programmatic payment verification endpoints."""

    authority = serializers.CharField(max_length=128, required=True)
    status = serializers.CharField(max_length=20, required=False, default="OK")
    gateway_ref = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    tracking_code = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")

