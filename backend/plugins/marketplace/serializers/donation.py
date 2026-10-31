from rest_framework import serializers
from ..models.donation import DonationRequest, Donation
from .base import BaseModelSerializer, BaseInputSerializer
from .catalog import ItemListSerializer
from .location import AddressSerializer


class DonationRequestSerializer(BaseModelSerializer):
    item = ItemListSerializer(read_only=True)
    requester_name = serializers.CharField(source="requester.get_full_name", read_only=True)

    class Meta:
        model = DonationRequest
        fields = [
            "id",
            "item",
            "requester",
            "requester_name",
            "message",
            "status",
            "created_at",
        ]


class SubmitDonationRequestInputSerializer(BaseInputSerializer):
    item_id = serializers.IntegerField(required=True)
    message = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class AcceptDonationRequestInputSerializer(BaseInputSerializer):
    shipping_address_id = serializers.IntegerField(required=False, allow_null=True)
    shipping_payer = serializers.ChoiceField(
        choices=Donation.ShippingPayer.choices,
        default=Donation.ShippingPayer.RECIPIENT
    )


class DonationSerializer(BaseModelSerializer):
    item = ItemListSerializer(read_only=True)
    donor_name = serializers.CharField(source="donor.get_full_name", read_only=True)
    recipient_name = serializers.CharField(source="recipient.get_full_name", read_only=True)
    shipping_address = AddressSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = [
            "id",
            "item",
            "donor",
            "donor_name",
            "recipient",
            "recipient_name",
            "status",
            "shipping_address",
            "shipping_payer",
            "tracking_code",
            "accepted_at",
            "shipped_at",
            "delivered_at",
        ]
