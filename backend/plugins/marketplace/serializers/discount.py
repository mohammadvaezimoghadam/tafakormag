from rest_framework import serializers
from ..models.discount import Coupon, CouponUsage
from .base import BaseModelSerializer, BaseInputSerializer


class CouponSerializer(BaseModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "title",
            "discount_type",
            "discount_value",
            "max_discount_amount",
            "min_order_amount",
            "valid_from",
            "valid_until",
            "is_active",
        ]


class ValidateCouponInputSerializer(BaseInputSerializer):
    code = serializers.CharField(max_length=50, required=True)
