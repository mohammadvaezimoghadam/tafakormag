from rest_framework import serializers
from ..models.location import Province, City, Address
from .base import BaseModelSerializer


class ProvinceSerializer(BaseModelSerializer):
    class Meta:
        model = Province
        fields = ["id", "name"]


class CitySerializer(BaseModelSerializer):
    province_name = serializers.CharField(source="province.name", read_only=True)

    class Meta:
        model = City
        fields = ["id", "province", "province_name", "name"]


class AddressSerializer(BaseModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    province_name = serializers.CharField(source="city.province.name", read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Address
        fields = [
            "id",
            "user",
            "title",
            "receiver_name",
            "receiver_phone",
            "city",
            "city_name",
            "province_name",
            "postal_address",
            "postal_code",
            "is_default",
            "created_at",
            "updated_at",
        ]

    def validate_postal_code(self, value: str):
        cleaned = value.strip().replace(" ", "").replace("-", "")
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise serializers.ValidationError("کد پستی باید دقیقاً یک عدد ۱۰ رقمی معتبر باشد.")
        return cleaned

    def validate_receiver_phone(self, value: str):
        cleaned = value.strip()
        if not (cleaned.startswith("09") and len(cleaned) == 11 and cleaned.isdigit()):
            raise serializers.ValidationError("شماره موبایل گیرنده باید با ۰۹ شروع شده و ۱۱ رقم باشد.")
        return cleaned

    def create(self, validated_data):
        # If set as default address, clear default flag from other user addresses
        is_default = validated_data.get("is_default", False)
        user = validated_data.get("user")
        if is_default and user:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        is_default = validated_data.get("is_default", instance.is_default)
        if is_default:
            Address.objects.filter(user=instance.user, is_default=True).exclude(id=instance.id).update(is_default=False)
        return super().update(instance, validated_data)
