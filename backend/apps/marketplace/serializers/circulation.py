from rest_framework import serializers
from ..models.circulation import (
    BookTitle,
    BookStation,
    PhysicalCopy,
    Transfer,
    Badge,
    BadgeAward,
)
from .base import BaseModelSerializer, BaseInputSerializer, UserDisplayNameField
from .location import CitySerializer


class BookTitleSerializer(BaseModelSerializer):
    class Meta:
        model = BookTitle
        fields = [
            "id",
            "title",
            "author",
            "translator",
            "publisher",
            "category",
            "isbn",
            "publication_year",
            "edition",
            "description",
            "cover_image",
            "source",
            "verified_by_admin",
            "created_at",
        ]


class BookTitleCreateInputSerializer(BaseInputSerializer):
    title = serializers.CharField(max_length=255, required=True)
    author = serializers.CharField(max_length=150, required=True)
    translator = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    publisher = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    category = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    isbn = serializers.CharField(max_length=25, required=False, allow_blank=True, default=None)
    publication_year = serializers.IntegerField(required=False, allow_null=True)
    edition = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")
    cover_image = serializers.FileField(required=False, allow_null=True)


class BookStationSerializer(BaseModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    current_books_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = BookStation
        fields = [
            "id",
            "name",
            "city",
            "city_name",
            "address_text",
            "latitude",
            "longitude",
            "capacity",
            "current_books_count",
            "is_active",
            "created_at",
        ]


class RegisterPhysicalCopyInputSerializer(BaseInputSerializer):
    book_title_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    author = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    publisher = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)
    cover_image = serializers.FileField(required=False, allow_null=True, default=None)
    condition = serializers.ChoiceField(
        choices=PhysicalCopy.Condition.choices,
        default=PhysicalCopy.Condition.GOOD
    )
    privacy = serializers.ChoiceField(
        choices=PhysicalCopy.Privacy.choices,
        default=PhysicalCopy.Privacy.FIRST_NAME_ONLY
    )

    def validate(self, attrs):
        if not attrs.get("book_title_id") and not (attrs.get("title") or "").strip():
            raise serializers.ValidationError("شناسه کتاب (book_title_id) یا عنوان کتاب (title) الزامی است.")
        return attrs


class PhysicalCopyListSerializer(BaseModelSerializer):
    book_title = BookTitleSerializer(read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True, default=None)
    is_holder = serializers.SerializerMethodField()
    can_claim = serializers.SerializerMethodField()

    class Meta:
        model = PhysicalCopy
        fields = [
            "id",
            "short_code",
            "book_title",
            "status",
            "condition",
            "station",
            "station_name",
            "transfer_count",
            "privacy",
            "is_holder",
            "can_claim",
            "created_at",
        ]

    def get_is_holder(self, obj) -> bool:
        user = self.current_user
        return bool(user and obj.current_holder_id == user.id)

    def get_can_claim(self, obj) -> bool:
        user = self.current_user
        if not user or obj.current_holder_id == user.id:
            return False
        return obj.status in [PhysicalCopy.Status.ACTIVE, PhysicalCopy.Status.IN_STATION]


class PhysicalCopyDetailSerializer(BaseModelSerializer):
    book_title = BookTitleSerializer(read_only=True)
    station = BookStationSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_holder = serializers.SerializerMethodField()
    can_claim = serializers.SerializerMethodField()
    active_transfer_id = serializers.SerializerMethodField()
    active_transfer = serializers.SerializerMethodField()

    class Meta:
        model = PhysicalCopy
        fields = [
            "id",
            "short_code",
            "book_title",
            "status",
            "status_display",
            "condition",
            "station",
            "transfer_count",
            "privacy",
            "is_holder",
            "can_claim",
            "active_transfer_id",
            "active_transfer",
            "created_at",
        ]

    def get_is_holder(self, obj) -> bool:
        user = self.current_user
        return bool(user and obj.current_holder_id == user.id)

    def get_can_claim(self, obj) -> bool:
        user = self.current_user
        if not user or obj.current_holder_id == user.id:
            return False
        return obj.status in [PhysicalCopy.Status.ACTIVE, PhysicalCopy.Status.IN_STATION]

    def get_active_transfer_id(self, obj):
        active = getattr(obj, "_active_transfer", None)
        if active:
            return active.id
        return None

    def get_active_transfer(self, obj):
        active = getattr(obj, "_active_transfer", None)
        if active:
            return TransferSerializer(active, context=self.context).data
        return None


class InitiateHandoverInputSerializer(BaseInputSerializer):
    short_code = serializers.CharField(max_length=20, required=True)
    recipient_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default=None)
    recipient_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    method = serializers.ChoiceField(
        choices=[Transfer.Method.SCAN_CONFIRM, Transfer.Method.OTP_FALLBACK],
        default=Transfer.Method.SCAN_CONFIRM
    )
    quantity = serializers.IntegerField(min_value=1, max_value=10000, required=False, default=1)
    donor_note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")


class ClaimCopyInputSerializer(BaseInputSerializer):
    short_code = serializers.CharField(max_length=20, required=True)
    quantity = serializers.IntegerField(min_value=1, max_value=10000, required=False, default=1)
    recipient_note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")


class ConfirmHandoverInputSerializer(BaseInputSerializer):
    otp_code = serializers.CharField(max_length=10, required=False, allow_blank=True, default=None)
    quantity = serializers.IntegerField(min_value=1, max_value=10000, required=False, allow_null=True, default=None)
    donor_note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")
    recipient_note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")


class StationDepositInputSerializer(BaseInputSerializer):
    short_code = serializers.CharField(max_length=20, required=True)
    station_id = serializers.IntegerField(required=True)
    donor_note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")


class StationPickupInputSerializer(BaseInputSerializer):
    short_code = serializers.CharField(max_length=20, required=True)
    recipient_note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")


class TransferSerializer(BaseModelSerializer):
    copy_short_code = serializers.CharField(source="copy.short_code", read_only=True)
    book_title_name = serializers.CharField(source="copy.book_title.title", read_only=True)
    book_author = serializers.CharField(source="copy.book_title.author", read_only=True)
    from_user_name = UserDisplayNameField("from_user", fallback="قفسه تفاخر")
    to_user_name = UserDisplayNameField("to_user", fallback="قفسه تفاخر")
    station_name = serializers.CharField(source="station.name", read_only=True, default=None)

    class Meta:
        model = Transfer
        fields = [
            "id",
            "copy",
            "copy_short_code",
            "book_title_name",
            "book_author",
            "from_user",
            "from_user_name",
            "to_user",
            "to_user_name",
            "station",
            "station_name",
            "method",
            "status",
            "quantity",
            "donor_note",
            "recipient_note",
            "otp_expires_at",
            "confirmed_at",
            "created_at",
        ]


class BadgeSerializer(BaseModelSerializer):
    class Meta:
        model = Badge
        fields = [
            "id",
            "slug",
            "title_fa",
            "title_en",
            "description_fa",
            "description_en",
            "icon",
            "threshold",
            "criteria",
            "order",
        ]


class BadgeAwardSerializer(BaseModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = BadgeAward
        fields = [
            "id",
            "badge",
            "created_at",
        ]

