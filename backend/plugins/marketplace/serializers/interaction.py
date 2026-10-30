from rest_framework import serializers
from ..models.interaction import Review, Wishlist, DigitalAccess
from .base import BaseModelSerializer
from .catalog import ItemListSerializer


class ReviewSerializer(BaseModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.get_full_name", read_only=True)
    reviewer = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Review
        fields = [
            "id",
            "item",
            "reviewer",
            "reviewer_name",
            "rating",
            "comment",
            "created_at",
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("امتیاز باید بین ۱ تا ۵ ستاره باشد.")
        return value


class WishlistSerializer(BaseModelSerializer):
    item = ItemListSerializer(read_only=True)
    item_id = serializers.IntegerField(write_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Wishlist
        fields = ["id", "user", "item", "item_id", "created_at"]


class DigitalAccessSerializer(BaseModelSerializer):
    item = ItemListSerializer(read_only=True)
    remaining_downloads = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = DigitalAccess
        fields = [
            "id",
            "item",
            "granted_via",
            "download_count",
            "max_downloads",
            "remaining_downloads",
            "is_expired",
            "expires_at",
            "last_downloaded_at",
            "created_at",
        ]

    def get_remaining_downloads(self, obj) -> int:
        return max(0, obj.max_downloads - obj.download_count)

    def get_is_expired(self, obj) -> bool:
        from django.utils import timezone
        if obj.expires_at and timezone.now() > obj.expires_at:
            return True
        return obj.download_count >= obj.max_downloads
