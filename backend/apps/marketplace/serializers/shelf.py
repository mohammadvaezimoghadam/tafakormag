from rest_framework import serializers

from ..models.catalog import Item
from ..models.circulation import PhysicalCopy
from ..models.donation import Donation
from ..models.shelf import UserShelfBook
from .base import BaseInputSerializer, BaseModelSerializer
from .circulation import BookTitleSerializer


_DONATION_METHOD_LABELS = {
    Item.DonationMethod.IN_PERSON: "اهدای حضوری (کد گردش QR)",
    Item.DonationMethod.POSTAL: "ارسال پستی",
    Item.DonationMethod.STATION: "ایستگاه / قفسه تفاخر",
    Item.DonationMethod.DIGITAL: "نسخه دیجیتال",
}


class _ShelfLinkedCopySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    short_code = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    transfer_count = serializers.IntegerField(read_only=True)
    station_id = serializers.IntegerField(read_only=True)
    station_name = serializers.SerializerMethodField()
    is_transferred_away = serializers.SerializerMethodField()

    def get_station_name(self, obj) -> str | None:
        if obj.station_id and obj.station:
            return obj.station.name
        return None

    def get_is_transferred_away(self, obj) -> bool:
        shelf_user_id = self.context.get("shelf_user_id")
        if shelf_user_id is None:
            return False
        if obj.status == PhysicalCopy.Status.IN_STATION:
            return False
        return obj.current_holder_id != shelf_user_id


class _ShelfLinkedItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    deal_type = serializers.CharField(read_only=True)
    deal_type_display = serializers.CharField(source="get_deal_type_display", read_only=True)
    delivery_type = serializers.CharField(read_only=True)
    donation_methods = serializers.SerializerMethodField()
    donation_method_labels = serializers.SerializerMethodField()
    shipping_payer = serializers.CharField(read_only=True)
    book_station_id = serializers.IntegerField(read_only=True)
    book_station_name = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=14, decimal_places=0, read_only=True)
    stock = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    category = serializers.IntegerField(source="category_id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default="")

    def get_donation_methods(self, obj):
        return obj.get_effective_donation_methods()

    def get_donation_method_labels(self, obj):
        return [_DONATION_METHOD_LABELS.get(m, m) for m in obj.get_effective_donation_methods()]

    def get_book_station_name(self, obj):
        if obj.book_station_id and obj.book_station:
            return obj.book_station.name
        return None


class ShelfBookSerializer(BaseModelSerializer):
    """
    Full owner serializer for personal bookshelf entries.
    """
    book_title = BookTitleSerializer(read_only=True)
    book_format_display = serializers.CharField(source="get_book_format_display", read_only=True)
    reading_status_display = serializers.CharField(source="get_reading_status_display", read_only=True)
    disposition_display = serializers.CharField(source="get_disposition_display", read_only=True)
    condition_display = serializers.CharField(source="get_condition_display", read_only=True, default=None)
    donation_methods = serializers.SerializerMethodField()
    donation_method_labels = serializers.SerializerMethodField()
    preferred_station_summary = serializers.SerializerMethodField()
    physical_copy_summary = serializers.SerializerMethodField()
    marketplace_item_summary = serializers.SerializerMethodField()
    reserved_quantity = serializers.IntegerField(read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    donated_count = serializers.IntegerField(read_only=True)
    is_gift = serializers.BooleanField(read_only=True)
    can_donate = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    gifted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = UserShelfBook
        fields = [
            "id",
            "book_title",
            "book_format",
            "book_format_display",
            "reading_status",
            "reading_status_display",
            "disposition",
            "disposition_display",
            "donation_methods",
            "donation_method_labels",
            "shipping_payer",
            "preferred_station_summary",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "donated_count",
            "is_gift",
            "can_donate",
            "can_edit",
            "can_delete",
            "gifted_by_name",
            "condition",
            "condition_display",
            "personal_note",
            "digital_reference",
            "acquired_from",
            "rating",
            "physical_copy_summary",
            "marketplace_item_summary",
            "created_at",
            "updated_at",
        ]

    def get_donation_methods(self, obj):
        return obj.get_effective_donation_methods()

    def get_donation_method_labels(self, obj):
        return [_DONATION_METHOD_LABELS.get(m, m) for m in obj.get_effective_donation_methods()]

    def get_preferred_station_summary(self, obj):
        st = obj.preferred_station
        if not st:
            return None
        return {
            "id": st.id,
            "name": st.name,
            "city_name": st.city.name if st.city_id else "",
            "address_text": st.address_text,
        }

    def get_physical_copy_summary(self, obj):
        copy = obj.physical_copy
        if not copy:
            copy = obj.book_title.physical_copies.filter(
                current_holder_id=obj.user_id,
                status="active"
            ).first()
        if not copy and obj.book_format == "physical" and obj.available_quantity > 0:
            from ..services.circulation_service import CirculationService
            try:
                copy = CirculationService.register_physical_copy(
                    user=obj.user,
                    book_title_id=obj.book_title_id,
                    condition=obj.condition or PhysicalCopy.Condition.NEW,
                )
                obj.physical_copy = copy
                obj.save(update_fields=["physical_copy"])
            except Exception:
                copy = None
        if not copy:
            return None
        return _ShelfLinkedCopySerializer(
            copy,
            context={"shelf_user_id": obj.user_id},
        ).data

    def get_marketplace_item_summary(self, obj):
        item = obj.marketplace_item
        if not item or item.is_deleted:
            return None
        return _ShelfLinkedItemSerializer(item).data

    def get_gifted_by_name(self, obj) -> str | None:
        if obj.is_gift:
            if obj.gifted_by:
                return obj.gifted_by.get_full_name() or getattr(obj.gifted_by, "username", "") or "ادمین تفکر"
            return "ادمین تفکر"
        return None

    def get_can_donate(self, obj) -> bool:
        return False

    def get_can_edit(self, obj) -> bool:
        return False

    def get_can_delete(self, obj) -> bool:
        return False


class ShelfBookCreateInputSerializer(BaseInputSerializer):
    book_title_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    author = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    translator = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    publisher = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    category = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    isbn = serializers.CharField(max_length=25, required=False, allow_blank=True, default=None)
    publication_year = serializers.IntegerField(required=False, allow_null=True)
    edition = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")

    book_format = serializers.ChoiceField(
        choices=UserShelfBook.BookFormat.choices,
        default=UserShelfBook.BookFormat.PHYSICAL,
    )
    reading_status = serializers.ChoiceField(
        choices=UserShelfBook.ReadingStatus.choices,
        default=UserShelfBook.ReadingStatus.IN_SHELF,
    )
    quantity = serializers.IntegerField(min_value=1, max_value=10000, required=False, default=1)
    condition = serializers.ChoiceField(
        choices=PhysicalCopy.Condition.choices,
        required=False,
        allow_null=True,
    )
    personal_note = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
    digital_reference = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    acquired_from = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    cover_image = serializers.FileField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get("book_title_id"):
            if not (attrs.get("title") or "").strip() or not (attrs.get("author") or "").strip():
                raise serializers.ValidationError(
                    "عنوان کتاب و نام نویسنده (یا شناسه شناسنامه کتاب) الزامی است."
                )
        return attrs


class ShelfBookUpdateInputSerializer(BaseInputSerializer):
    book_format = serializers.ChoiceField(choices=UserShelfBook.BookFormat.choices, required=False)
    reading_status = serializers.ChoiceField(choices=UserShelfBook.ReadingStatus.choices, required=False)
    quantity = serializers.IntegerField(min_value=1, max_value=10000, required=False)
    condition = serializers.ChoiceField(
        choices=PhysicalCopy.Condition.choices,
        required=False,
        allow_null=True,
    )
    personal_note = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    digital_reference = serializers.CharField(max_length=500, required=False, allow_blank=True)
    acquired_from = serializers.CharField(max_length=150, required=False, allow_blank=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    cover_image = serializers.FileField(required=False, allow_null=True)


class ShelfStartCirculationInputSerializer(BaseInputSerializer):
    condition = serializers.ChoiceField(
        choices=PhysicalCopy.Condition.choices,
        required=False,
        allow_null=True,
    )
    privacy = serializers.ChoiceField(
        choices=PhysicalCopy.Privacy.choices,
        default=PhysicalCopy.Privacy.FIRST_NAME_ONLY,
    )


class ShelfPublishListingInputSerializer(BaseInputSerializer):
    deal_type = serializers.ChoiceField(
        choices=[Item.DealType.DONATION, Item.DealType.SALE],
        required=True,
    )
    price = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        required=False,
        allow_null=True,
        default=0,
        min_value=0,
    )
    donation_methods = serializers.ListField(
        child=serializers.ChoiceField(choices=Item.DonationMethod.choices),
        required=False,
        allow_empty=True,
        default=list,
    )
    station_id = serializers.IntegerField(required=False, allow_null=True)
    deposit_now = serializers.BooleanField(required=False, default=False)
    shipping_payer = serializers.ChoiceField(
        choices=Donation.ShippingPayer.choices,
        required=False,
        default=Donation.ShippingPayer.RECIPIENT,
    )
    privacy = serializers.ChoiceField(
        choices=PhysicalCopy.Privacy.choices,
        required=False,
        default=PhysicalCopy.Privacy.FIRST_NAME_ONLY,
    )
    category_id = serializers.IntegerField(required=False, allow_null=True)
    topic_id = serializers.IntegerField(required=False, allow_null=True)
    city_id = serializers.IntegerField(required=False, allow_null=True)
    stock = serializers.IntegerField(min_value=1, max_value=10000, required=False, default=1)
    weight_grams = serializers.IntegerField(min_value=0, required=False, default=0)
    description = serializers.CharField(max_length=3000, required=False, allow_blank=True, default="")
    digital_file_key = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    file_format = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")


class ShelfDonateToPhoneInputSerializer(BaseInputSerializer):
    quantity = serializers.IntegerField(min_value=1, default=1, required=False)
    recipient_phone = serializers.CharField(max_length=20, required=True)
    send_sms = serializers.BooleanField(default=False, required=False)


class ShelfGiftActionInputSerializer(BaseInputSerializer):
    transfer_id = serializers.IntegerField(required=True)


class ShelfAdminDonateInputSerializer(BaseInputSerializer):
    quantity = serializers.IntegerField(min_value=1, default=1, required=False)
    recipient_phone = serializers.CharField(max_length=20, required=True)


class ShelfReturnDonationInputSerializer(BaseInputSerializer):
    short_code = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    transfer_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    quantity = serializers.IntegerField(min_value=1, default=1, required=False)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


