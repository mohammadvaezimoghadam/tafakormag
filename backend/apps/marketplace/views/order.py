from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models.order import Order
from ..services.order_service import OrderService
from ..serializers.order import (
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutInputSerializer,
)
from ..exceptions import MarketplaceError


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Order Management API for buyers:
    - View order history and shipment delivery packages.
    - Atomically converts active shopping cart to multi-vendor order.
    - Cancels unpaid pending orders.
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderListSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(buyer=self.request.user)
            .select_related("shipping_address", "coupon")
            .prefetch_related(
                "shipments__seller",
                "shipments__items__item",
                "status_history",
            )
            .order_by("-created_at")
        )

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        """
        Converts the user's shopping cart into an Order and splits into vendor shipments.
        """
        serializer = CheckoutInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        shipping_address_id = serializer.validated_data.get("shipping_address_id")
        coupon_code = serializer.validated_data.get("coupon_code")

        try:
            order = OrderService.create_order_from_cart(
                user=request.user,
                shipping_address_id=shipping_address_id,
                coupon_code=coupon_code,
            )
            detail_data = OrderDetailSerializer(order, context={"request": request}).data
            return Response(detail_data, status=status.HTTP_201_CREATED)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, order_number=None):
        """
        Cancels an unpaid order and releases reserved warehouse stock.
        """
        order = self.get_object()
        try:
            OrderService.cancel_order(order=order, reason="لغو توسط خریدار")
            detail_data = OrderDetailSerializer(order, context={"request": request}).data
            return Response(detail_data, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
