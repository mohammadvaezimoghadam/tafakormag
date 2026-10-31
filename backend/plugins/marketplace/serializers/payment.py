from rest_framework import serializers
from ..models.payment import Payment, SellerSettlement
from ..models.finance import SellerBankAccount
from .base import BaseModelSerializer, BaseInputSerializer


class SellerBankAccountSerializer(BaseModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SellerBankAccount
        fields = [
            "id",
            "user",
            "bank_name",
            "account_holder",
            "iban",
            "card_number",
            "is_verified",
            "created_at",
        ]

    def validate_iban(self, value: str):
        cleaned = value.strip().upper().replace(" ", "")
        if cleaned.startswith("IR"):
            cleaned = cleaned[2:]
        if not (cleaned.isdigit() and len(cleaned) == 24):
            raise serializers.ValidationError("شماره شبا باید شامل ۲۴ رقم عددی معتبر (بدون IR) باشد.")
        return f"IR{cleaned}"

    def validate_card_number(self, value: str):
        if not value:
            return ""
        cleaned = value.strip().replace("-", "").replace(" ", "")
        if not (cleaned.isdigit() and len(cleaned) == 16):
            raise serializers.ValidationError("شماره کارت باید ۱۶ رقم عددی باشد.")
        return cleaned


class PaymentSerializer(BaseModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_number",
            "amount",
            "gateway",
            "authority",
            "tracking_code",
            "status",
            "paid_at",
            "created_at",
        ]


class InitiatePaymentInputSerializer(BaseInputSerializer):
    order_id = serializers.IntegerField(required=True)
    callback_url = serializers.URLField(required=True)
    gateway = serializers.CharField(required=False, default="zarinpal")


class VerifyPaymentInputSerializer(BaseInputSerializer):
    authority = serializers.CharField(max_length=100, required=True)
    status = serializers.CharField(max_length=20, required=False, default="OK")


class SellerSettlementSerializer(BaseModelSerializer):
    shipment_id = serializers.IntegerField(source="shipment.id", read_only=True)
    order_number = serializers.CharField(source="shipment.order.order_number", read_only=True)

    class Meta:
        model = SellerSettlement
        fields = [
            "id",
            "shipment_id",
            "order_number",
            "gross_amount",
            "platform_fee",
            "seller_discount_share",
            "net_amount",
            "status",
            "settled_at",
            "created_at",
        ]
