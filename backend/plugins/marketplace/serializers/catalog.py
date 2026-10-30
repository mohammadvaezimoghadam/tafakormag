from rest_framework import serializers
from decimal import Decimal
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
    cover_image = serializers.SerializerMethodField()
    effective_price = serializers.SerializerMethodField()
    has_active_discount = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "category_name",
            "seller_name",
            "deal_type",
            "delivery_type",
            "condition",
            "price",
            "discount_price",
            "effective_price",
            "has_active_discount",
            "stock",
            "is_unlimited_stock",
            "status",
            "cover_image",
            "views_count",
            "is_featured",
            "created_at",
        ]

    def get_seller_name(self, obj):
        return obj.seller.get_full_name() or obj.seller.phone

    def get_cover_image(self, obj):
        if hasattr(obj, "cover_images") and obj.cover_images:
            return obj.cover_images[0].image_url if obj.cover_images[0].image_url else None
        cover = obj.images.filter(is_cover=True).first()
        if cover and cover.image_url:
            return cover.image_url
        first_img = obj.images.first()
        if first_img:
            return first_img.image_url
        return None

    def get_effective_price(self, obj) -> Decimal:
        if obj.discount_price and (not obj.discount_ends_at or timezone.now() < obj.discount_ends_at):
            return obj.discount_price
        return obj.price

    def get_has_active_discount(self, obj) -> bool:
        return bool(obj.discount_price and (not obj.discount_ends_at or timezone.now() < obj.discount_ends_at))


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
            "is_featured",
            "status",
        ]

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

        return attrs

    def create(self, validated_data):
        book_metadata = validated_data.pop("book_metadata", None)
        images = validated_data.pop("images", [])
        cover_image_url = validated_data.pop("cover_image_url", None)

        item = super().create(validated_data)

        if book_metadata:
            BookDetail.objects.create(item=item, **book_metadata)

        if cover_image_url:
            ItemImage.objects.create(item=item, image_url=cover_image_url, is_cover=True, sort_order=0)

        for idx, img in enumerate(images):
            if isinstance(img, dict):
                url = img.get("image_url") or img.get("url")
                is_cov = img.get("is_cover", (idx == 0 and not cover_image_url))
            else:
                url = str(img)
                is_cov = (idx == 0 and not cover_image_url)
            if url:
                ItemImage.objects.create(item=item, image_url=url, is_cover=is_cov, sort_order=idx)

        return item

    def update(self, instance, validated_data):
        book_metadata = validated_data.pop("book_metadata", None)
        images = validated_data.pop("images", None)
        cover_image_url = validated_data.pop("cover_image_url", None)

        item = super().update(instance, validated_data)

        if book_metadata is not None:
            BookDetail.objects.update_or_create(item=item, defaults=book_metadata)

        if cover_image_url:
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
