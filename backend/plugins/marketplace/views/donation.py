from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models.donation import DonationRequest, Donation
from ..services.donation_service import DonationService
from ..serializers.donation import (
    DonationRequestSerializer,
    SubmitDonationRequestInputSerializer,
    AcceptDonationRequestInputSerializer,
    DonationSerializer,
)
from ..exceptions import MarketplaceError


class DonationRequestViewSet(viewsets.ModelViewSet):
    """
    Manages peer-to-peer donation requests:
    - Recipients submit and view their requests.
    - Donors inspect incoming requests for their donated books.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DonationRequestSerializer

    def get_queryset(self):
        # Shows requests sent by this user OR received for items owned by this user
        return (
            DonationRequest.objects.filter(
                requester=self.request.user
            ) | DonationRequest.objects.filter(
                item__seller=self.request.user
            )
        ).select_related("item", "requester").distinct().order_by("-created_at")

    def create(self, request, *args, **kwargs):
        """
        Submits a new request for a donated book.
        """
        serializer = SubmitDonationRequestInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        item_id = serializer.validated_data["item_id"]
        message = serializer.validated_data.get("message", "")

        try:
            req = DonationService.submit_request(
                user=request.user,
                item_id=item_id,
                message=message,
            )
            return Response(DonationRequestSerializer(req).data, status=status.HTTP_201_CREATED)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        """
        Donor accepts a specific request, fulfilling digital or physical donation.
        """
        serializer = AcceptDonationRequestInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        shipping_address_id = serializer.validated_data.get("shipping_address_id")
        shipping_payer = serializer.validated_data.get("shipping_payer", Donation.ShippingPayer.RECIPIENT)

        try:
            donation = DonationService.accept_request(
                donor_user=request.user,
                request_id=int(pk),
                shipping_address_id=shipping_address_id,
                shipping_payer=shipping_payer,
            )
            return Response(DonationSerializer(donation).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        """
        Donor rejects a specific request.
        """
        try:
            req = DonationService.reject_request(donor_user=request.user, request_id=int(pk))
            return Response(DonationRequestSerializer(req).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)


class DonationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Manages confirmed donation records and shipping progress for both donor and recipient.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DonationSerializer

    def get_queryset(self):
        return (
            Donation.objects.filter(donor=self.request.user)
            | Donation.objects.filter(recipient=self.request.user)
        ).select_related("item", "donor", "recipient", "shipping_address").distinct().order_by("-accepted_at")

    @action(detail=True, methods=["post"], url_path="ship")
    def ship(self, request, pk=None):
        """
        Donor inputs postal tracking code.
        """
        tracking_code = request.data.get("tracking_code", "").strip()
        if not tracking_code:
            return Response({"detail": "کد رهگیری پستی الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            donation = DonationService.mark_as_shipped(
                donor_user=request.user,
                donation_id=int(pk),
                tracking_code=tracking_code,
            )
            return Response(DonationSerializer(donation).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="confirm-delivery")
    def confirm_delivery(self, request, pk=None):
        """
        Recipient acknowledges delivery of the donated book.
        """
        try:
            donation = DonationService.confirm_delivery(
                recipient_user=request.user,
                donation_id=int(pk),
            )
            return Response(DonationSerializer(donation).data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
