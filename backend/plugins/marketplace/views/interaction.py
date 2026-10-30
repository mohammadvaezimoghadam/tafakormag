from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from ..models.interaction import Review, Wishlist, DigitalAccess
from ..models.order import Order
from ..models.donation import Donation
from ..serializers.interaction import (
    ReviewSerializer,
    WishlistSerializer,
    DigitalAccessSerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Customer reviews API:
    - Public read for item reviews.
    - Authenticated creation with verification of purchase/donation history.
    """
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Review.objects.select_related("reviewer").order_by("-created_at")
        item_id = self.request.query_params.get("item_id")
        if item_id and item_id.isdigit():
            qs = qs.filter(item_id=int(item_id))
        return qs

    def perform_create(self, serializer):
        item = serializer.validated_data["item"]
        user = self.request.user

        # Find matching paid order or completed donation for verification
        verified_order = Order.objects.filter(
            buyer=user,
            status=Order.Status.PAID,
            items__item=item
        ).first()

        verified_donation = Donation.objects.filter(
            recipient=user,
            item=item,
            status=Donation.Status.DELIVERED
        ).first()

        serializer.save(
            reviewer=user,
            order=verified_order,
            donation=verified_donation
        )


class WishlistViewSet(viewsets.ModelViewSet):
    """
    User favorites / wishlist API.
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related("item", "item__category").order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DigitalAccessViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Authorized digital library API for purchased or donated eBooks / audio files.
    """
    serializer_class = DigitalAccessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DigitalAccess.objects.filter(user=self.request.user).select_related("item").order_by("-created_at")

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        """
        Validates access expiration and download caps, then issues secure download token.
        """
        access = self.get_object()

        if access.expires_at and timezone.now() > access.expires_at:
            return Response({"detail": "مهلت دسترسی شما به این فایل به پایان رسیده است."}, status=status.HTTP_403_FORBIDDEN)

        if access.download_count >= access.max_downloads:
            return Response({"detail": "سقف دفعات مجاز دانلود برای این فایل تکمیل شده است."}, status=status.HTTP_403_FORBIDDEN)

        access.download_count += 1
        access.last_downloaded_at = timezone.now()
        access.save(update_fields=["download_count", "last_downloaded_at"])

        return Response({
            "title": access.item.title,
            "file_format": access.item.file_format,
            "download_url": f"/media/secure/{access.item.digital_file_key}",
            "remaining_downloads": access.max_downloads - access.download_count,
        }, status=status.HTTP_200_OK)
