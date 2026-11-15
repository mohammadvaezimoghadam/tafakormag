import os
import uuid
from rest_framework import serializers
from decimal import Decimal
from django.core.files.storage import default_storage
from django.utils import timezone

from ..models.catalog import Category, Item, ItemImage, BookDetail, ItemAttribute
from .base import BaseModelSerializer


class CategorySerializer(BaseModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "parent", "children", "order"]

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class ItemImageSerializer(BaseModelSerializer):
    class Meta:
        model = ItemImage
        fields = ["id", "image_url", "is_cover", "sort_order"]


class BookDetailSerializer(BaseModelSerializer):
    class Meta:
        model = BookDetail
        fields = [
            "author",
            "translator",
            "publisher",
            "isbn",
            "publication_year",
            "pages_count",
        ]


class ItemAttributeSerializer(BaseModelSerializer):
    class Meta:
        model = ItemAttribute
        fields = ["id", "attribute_key", "attribute_value"]


class ItemListSerializer(BaseModelSerializer):
    """
    Lightweight listing serializer optimized for catalog cards, search, and feeds.
    Minimizes DB lookups when combined with select_related / prefetch_related.
    """
    category_name = serializers.CharField(source="category.name", read_only=True)
    seller_name = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    book_title_id = serializers.IntegerField(read_only=True)
    cover_image = serializers.SerializerMethodField()
    effective_price = serializers.SerializerMethodField()
    has_active_discount = serializers.SerializerMethodField()
    badge_label = serializers.SerializerMethodField()
    badge_color = serializers.SerializerMethodField()
    deal_type_display = serializers.CharField(source="get_deal_type_display", read_only=True)
    donation_methods = serializers.SerializerMethodField()
    donation_method_labels = serializers.SerializerMethodField()
    physical_copy_summary = serializers.SerializerMethodField()
    station_summary = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "book_title_id",
            "category",
            "category_name",
            "seller",
            "seller_name",
            "deal_type",
            "deal_type_display",
            "delivery_type",
            "donation_methods",
            "donation_method_labels",
            "shipping_payer",
            "physical_copy_summary",
            "station_summary",
            "condition",
            "price",
            "discount_price",
            "effective_price",
            "has_active_discount",
            "badge_label",
            "badge_color",
            "stock",
            "is_unlimited_stock",
            "status",
            "cover_image",
            "views_count",
            "is_featured",
            "created_at",
        ]

    def get_seller_name(self, obj):
        return self.format_user_display_name(obj.seller)

    def get_author(self, obj):
        if obj.book_title_id and obj.book_title:
            return obj.book_title.author
        try:
            if obj.book_detail and obj.book_detail.author:
                return obj.book_detail.author
        except Exception:
            pass
        return None

    def get_donation_methods(self, obj):
        return obj.get_effective_donation_methods()

    def get_donation_method_labels(self, obj):
        return [
            Item.DONATION_METHOD_SHORT_LABELS.get(m, m)
            for m in obj.get_effective_donation_methods()
        ]

    def get_physical_copy_summary(self, obj):
        copy = getattr(obj, "physical_copy", None)
        if not copy:
            return None
        return {
            "id": str(copy.id),
            "short_code": copy.short_code,
            "status": copy.status,
            "transfer_count": copy.transfer_count,
        }

    def get_station_summary(self, obj):
        st = getattr(obj, "book_station", None)
        if not st and obj.physical_copy_id and obj.physical_copy and obj.physical_copy.station_id:
            st = obj.physical_copy.station
        if not st:
            return None
        return {
            "id": st.id,
            "name": st.name,
            "city_name": st.city.name if st.city_id else "",
            "address_text": st.address_text,
        }

    def get_cover_image(self, obj):
        if hasattr(obj, "prefetched_images"):
            for img in obj.prefetched_images:
                if img.image_url:
                    return img.image_url
        elif hasattr(obj, "cover_images") and obj.cover_images:
            return obj.cover_images[0].image_url if obj.cover_images[0].image_url else None
        elif not hasattr(obj, "cover_images"):
            cover = obj.images.filter(is_cover=True).first()
            if cover and cover.image_url:
                return cover.image_url
            first_img = obj.images.first()
            if first_img and first_img.image_url:
                return first_img.image_url

        if obj.book_title_id and obj.book_title and obj.book_title.cover_image:
            try:
                return obj.book_title.cover_image.url
            except Exception:
                return None
        return None

    def get_effective_price(self, obj) -> Decimal:
        if obj.discount_price and (not obj.discount_ends_at or timezone.now() < obj.discount_ends_at):
            return obj.discount_price
        return obj.price

    def get_has_active_discount(self, obj) -> bool:
        return bool(obj.discount_price and (not obj.discount_ends_at or timezone.now() < obj.discount_ends_at))

    def get_badge_label(self, obj) -> str:
        if obj.deal_type == Item.DealType.DONATION:
            return "اهدای رایگان"
        eff_price = self.get_effective_price(obj)
        try:
            return f"فروشی: {int(eff_price):,} تومان"
        except (ValueError, TypeError):
            return f"فروشی: {eff_price} تومان"

    def get_badge_color(self, obj) -> str:
        if obj.deal_type == Item.DealType.DONATION:
            return "green"
        return "blue"


class ItemDetailSerializer(ItemListSerializer):
    """
    Full-depth detail serializer including high-res gallery images,
    specific book metadata, and custom EAV attributes.
    """
    images = ItemImageSerializer(many=True, read_only=True)
    book_detail = BookDetailSerializer(read_only=True)
    attributes = ItemAttributeSerializer(many=True, read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    province_name = serializers.CharField(source="city.province.name", read_only=True)

    class Meta(ItemListSerializer.Meta):
        fields = ItemListSerializer.Meta.fields + [
            "description",
            "city",
            "city_name",
            "province_name",
            "weight_grams",
            "images",
            "book_detail",
            "attributes",
        ]


class ItemCreateUpdateSerializer(BaseModelSerializer):
    """
    Serializer used by sellers to publish or update items.
    """
    seller = serializers.HiddenField(default=serializers.CurrentUserDefault())
    book_metadata = BookDetailSerializer(required=False, allow_null=True, write_only=True)
    images = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        write_only=True,
    )
    cover_image_url = serializers.CharField(
        max_length=500,
        required=False,
        write_only=True,
        allow_blank=True,
    )
    cover_image = serializers.FileField(
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Item
        fields = [
            "id",
            "seller",
            "category",
            "topic",
            "title",
            "description",
            "deal_type",
            "delivery_type",
            "donation_methods",
            "book_station",
            "shipping_payer",
            "condition",
            "price",
            "discount_price",
            "discount_ends_at",
            "stock",
            "is_unlimited_stock",
            "city",
            "weight_grams",
            "book_metadata",
            "images",
            "cover_image_url",
            "cover_image",
            "is_featured",
            "status",
        ]

    @staticmethod
    def _attach_uploaded_cover(item, uploaded_file):
        if not uploaded_file:
            return
        ext = os.path.splitext(getattr(uploaded_file, "name", "") or "")[1].lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            ext = ".png"
        storage_path = default_storage.save(
            f"marketplace/items/covers/{uuid.uuid4().hex}{ext}",
            uploaded_file,
        )
        saved_url = default_storage.url(storage_path)
        ItemImage.objects.filter(item=item, is_cover=True).update(is_cover=False)
        ItemImage.objects.create(item=item, image_url=saved_url, is_cover=True, sort_order=0)

    def validate(self, attrs):
        deal_type = attrs.get("deal_type", getattr(self.instance, "deal_type", Item.DealType.SALE))
        price = attrs.get("price", getattr(self.instance, "price", 0))

        if deal_type == Item.DealType.DONATION:
            attrs["price"] = Decimal("0")
            attrs["discount_price"] = None
        elif deal_type == Item.DealType.SALE and price <= 0:
            raise serializers.ValidationError({"price": "برای کالای فروشی، درج قیمت بزرگتر از صفر الزامی است."})

        delivery_type = attrs.get("delivery_type", getattr(self.instance, "delivery_type", Item.DeliveryType.PHYSICAL))
        if delivery_type == Item.DeliveryType.DIGITAL:
            attrs["weight_grams"] = 0

        if deal_type == Item.DealType.DONATION:
            raw_methods = attrs.get("donation_methods", getattr(self.instance, "donation_methods", None))
            station = attrs.get("book_station", getattr(self.instance, "book_station", None))
            attrs["donation_methods"] = Item.normalize_donation_methods(
                raw_methods,
                delivery_type=delivery_type,
                has_station=bool(station),
            )
        else:
            attrs["donation_methods"] = []

        return attrs

    def create(self, validated_data):
        book_metadata = validated_data.pop("book_metadata", None)
        images = validated_data.pop("images", [])
        cover_image_url = validated_data.pop("cover_image_url", None)
        cover_image_file = validated_data.pop("cover_image", None)

        item = super().create(validated_data)

        if book_metadata:
            BookDetail.objects.create(item=item, **book_metadata)

        if cover_image_file:
            self._attach_uploaded_cover(item, cover_image_file)
        elif cover_image_url:
            ItemImage.objects.create(item=item, image_url=cover_image_url, is_cover=True, sort_order=0)

        for idx, img in enumerate(images):
            if isinstance(img, dict):
                url = img.get("image_url") or img.get("url")
                is_cov = img.get("is_cover", (idx == 0 and not cover_image_url and not cover_image_file))
            else:
                url = str(img)
                is_cov = (idx == 0 and not cover_image_url and not cover_image_file)
            if url:
                ItemImage.objects.create(item=item, image_url=url, is_cover=is_cov, sort_order=idx)

        return item

    def update(self, instance, validated_data):
        book_metadata = validated_data.pop("book_metadata", None)
        images = validated_data.pop("images", None)
        cover_image_url = validated_data.pop("cover_image_url", None)
        cover_image_file = validated_data.pop("cover_image", None)

        item = super().update(instance, validated_data)

        if book_metadata is not None:
            BookDetail.objects.update_or_create(item=item, defaults=book_metadata)

        if cover_image_file:
            self._attach_uploaded_cover(item, cover_image_file)
        elif cover_image_url:
            ItemImage.objects.filter(item=item, is_cover=True).update(is_cover=False)
            ItemImage.objects.create(item=item, image_url=cover_image_url, is_cover=True, sort_order=0)

        if images is not None:
            for idx, img in enumerate(images):
                if isinstance(img, dict):
                    url = img.get("image_url") or img.get("url")
                    is_cov = img.get("is_cover", False)
                else:
                    url = str(img)
                    is_cov = False
                if url:
                    ItemImage.objects.create(item=item, image_url=url, is_cover=is_cov, sort_order=idx + 1)

        return item
