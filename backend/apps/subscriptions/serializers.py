from rest_framework import serializers
from django.utils import timezone
from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """سریالایزر نمایش پلن‌های اشتراک برای کلاینت فلاتر"""
    price_toman = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'plugin_identifier',
            'sku',
            'title',
            'description',
            'duration_days',
            'price',
            'price_toman',
            'features',
            'is_active',
        ]

    def get_price_toman(self, obj) -> int:
        """تبدیل ریال به تومان جهت نمایش در اپ فلاتر"""
        return int(obj.price // 10) if obj.price else 0


class UserSubscriptionStatusSerializer(serializers.Serializer):
    """سریالایزر استعلام وضعیت اشتراک کاربر در یک افزونه"""
    has_active_subscription = serializers.BooleanField()
    plugin_identifier = serializers.CharField()
    status = serializers.CharField()
    expires_at = serializers.DateTimeField(allow_null=True)
    remaining_days = serializers.IntegerField()
    plan_title = serializers.CharField(allow_null=True, required=False)
    sku = serializers.CharField(allow_null=True, required=False)


class PurchaseVerifyRequestSerializer(serializers.Serializer):
    """سریالایزر اعتبارسنجی ورودی درخواست وریفای توکن کافه‌بازار"""
    sku = serializers.CharField(
        max_length=150,
        required=True,
        help_text="شناسه بسته خریداری شده در کافه‌بازار (مانند sub_vip_1m)"
    )
    purchase_token = serializers.CharField(
        max_length=255,
        required=True,
        help_text="توکن یکتای بازگشتی از کتابخانه Poolakey کافه‌بازار"
    )
    marketplace = serializers.CharField(
        max_length=50,
        default='cafebazaar',
        required=False
    )
    package_name = serializers.CharField(
        max_length=150,
        required=False,
        default='com.tafakor.quran'
    )


class PurchaseVerifyResponseSerializer(serializers.Serializer):
    """سریالایزر پاسخ موفقیت‌آمیز وریفای خرید"""
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    subscription = UserSubscriptionStatusSerializer()
    verified_at = serializers.DateTimeField()

