from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notes.models import normalize_persian_text
from ..exceptions import MarketplaceError
from ..models.shelf import UserShelfBook
from ..permissions import IsShelfBookOwner
from ..serializers.shelf import (
    ShelfBookCreateInputSerializer,
    ShelfBookSerializer,
    ShelfBookUpdateInputSerializer,
    ShelfDonateToPhoneInputSerializer,
    ShelfGiftActionInputSerializer,
    ShelfPublishListingInputSerializer,
    ShelfStartCirculationInputSerializer,
)
from ..services.shelf_service import ShelfService


def _apply_shelf_search(qs, raw_query: str):
    q = (raw_query or "").strip()
    if not q:
        return qs
    norm_q = normalize_persian_text(q)
    return qs.filter(
        Q(book_title__normalized_title__icontains=norm_q)
        | Q(book_title__normalized_author__icontains=norm_q)
        | Q(book_title__normalized_translator__icontains=norm_q)
        | Q(book_title__publisher__icontains=q)
        | Q(book_title__publisher__icontains=norm_q)
        | Q(book_title__isbn__icontains=q)
    )


class UserShelfBookViewSet(viewsets.ModelViewSet):
    """
    Personal Bookshelf API (قفسه کتاب شخصی کاربر).
    Thin views strictly delegating business rules to ShelfService.
    """

    lookup_value_regex = r"\d+"
    permission_classes = [permissions.IsAuthenticated, IsShelfBookOwner]

    def _base_queryset(self):
        return UserShelfBook.objects.select_related(
            "user",
            "gifted_by",
            "book_title",
            "preferred_station",
            "preferred_station__city",
            "physical_copy",
            "physical_copy__current_holder",
            "physical_copy__station",
            "marketplace_item",
            "marketplace_item__category",
            "marketplace_item__book_station",
        ).order_by("-created_at")

    def get_queryset(self):
        qs = self._base_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs.none()

        qs = qs.filter(user=user)
        if self.action == "list":
            qs = _apply_shelf_search(qs, self.request.query_params.get("search", ""))
            for param, field in (
                ("reading_status", "reading_status"),
                ("disposition", "disposition"),
                ("book_format", "book_format"),
            ):
                val = (self.request.query_params.get(param) or "").strip()
                if val:
                    qs = qs.filter(**{field: val})

        return qs

    def get_serializer_class(self):
        return ShelfBookSerializer

    def create(self, request, *args, **kwargs):
        serializer = ShelfBookCreateInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            entry = ShelfService.add_book(user=request.user, data=serializer.validated_data)
            entry = self._base_queryset().get(id=entry.id)
            return Response(
                ShelfBookSerializer(entry, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = ShelfBookUpdateInputSerializer(
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            updated = ShelfService.update_book(
                user=request.user,
                shelf_book=instance,
                data=serializer.validated_data,
            )
            updated = self._base_queryset().get(id=updated.id)
            return Response(ShelfBookSerializer(updated, context={"request": request}).data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            ShelfService.remove_book(user=request.user, shelf_book=instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Returns aggregate personal bookshelf counters in a single SQL query."""
        stats = UserShelfBook.objects.filter(user=request.user).aggregate(
            total=Count("id"),
            total_copies=Coalesce(Sum("quantity"), 0),
            reading_count=Count("id", filter=Q(reading_status=UserShelfBook.ReadingStatus.READING)),
            finished_count=Count("id", filter=Q(reading_status=UserShelfBook.ReadingStatus.FINISHED)),
            want_to_read_count=Count("id", filter=Q(reading_status=UserShelfBook.ReadingStatus.WANT_TO_READ)),
            keeping_count=Count("id", filter=Q(disposition=UserShelfBook.Disposition.KEEPING)),
            offering_count=Count("id", filter=~Q(disposition=UserShelfBook.Disposition.KEEPING)),
        )
        return Response(stats)

    @action(detail=True, methods=["post"], url_path="start-circulation")
    def start_circulation(self, request, pk=None):
        """Registers or reactivates QR circulation (TK-XXXX) for a physical shelf book."""
        instance = self.get_object()
        serializer = ShelfStartCirculationInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            updated = ShelfService.start_circulation(
                user=request.user,
                shelf_book=instance,
                condition=serializer.validated_data.get("condition"),
                privacy=serializer.validated_data.get("privacy"),
            )
            updated = self._base_queryset().get(id=updated.id)
            return Response(ShelfBookSerializer(updated, context={"request": request}).data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="publish-listing")
    def publish_listing(self, request, pk=None):
        """Publishes a shelf book as a donation or sale listing in the marketplace catalog."""
        instance = self.get_object()
        serializer = ShelfPublishListingInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            updated = ShelfService.publish_to_marketplace(
                user=request.user,
                shelf_book=instance,
                data=serializer.validated_data,
            )
            updated = self._base_queryset().get(id=updated.id)
            return Response(ShelfBookSerializer(updated, context={"request": request}).data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="withdraw-offering")
    def withdraw_offering(self, request, pk=None):
        """Returns a shelf book back to purely personal keeping status."""
        instance = self.get_object()
        try:
            updated = ShelfService.withdraw_offering(user=request.user, shelf_book=instance)
            updated = self._base_queryset().get(id=updated.id)
            return Response(ShelfBookSerializer(updated, context={"request": request}).data)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="donate-to-phone")
    def donate_to_phone(self, request, pk=None):
        """Donates copies of a shelf book to a phone number (with optional async SMS)."""
        instance = self.get_object()
        serializer = ShelfDonateToPhoneInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            result = ShelfService.donate_to_phone(
                user=request.user,
                shelf_book=instance,
                quantity=serializer.validated_data.get("quantity", 1),
                recipient_phone=serializer.validated_data["recipient_phone"],
                send_sms=serializer.validated_data.get("send_sms", False),
            )
            return Response(result, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="incoming-gifts")
    def incoming_gifts(self, request):
        """Lists pending incoming book gifts for the authenticated user."""
        gifts = ShelfService.get_incoming_gifts(request.user)
        return Response(gifts, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="confirm-gift")
    def confirm_gift(self, request):
        """Recipient confirms receipt of a gifted book."""
        serializer = ShelfGiftActionInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            result = ShelfService.confirm_gift(
                user=request.user,
                transfer_id=serializer.validated_data["transfer_id"],
            )
            return Response(result, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="reject-gift")
    def reject_gift(self, request):
        """Recipient rejects a gifted book."""
        serializer = ShelfGiftActionInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            result = ShelfService.reject_gift(
                user=request.user,
                transfer_id=serializer.validated_data["transfer_id"],
            )
            return Response(result, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="cancel-gift")
    def cancel_gift(self, request):
        """Donor cancels a pending book gift."""
        serializer = ShelfGiftActionInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            result = ShelfService.cancel_gift(
                user=request.user,
                transfer_id=serializer.validated_data["transfer_id"],
            )
            return Response(result, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
