from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models.order import Order
from ..services.payment_service import PaymentService
from ..serializers.payment import (
    InitiatePaymentInputSerializer,
    VerifyPaymentInputSerializer,
)
from ..exceptions import MarketplaceError


class PaymentViewSet(viewsets.ViewSet):
    """
    Financial Payment Gateway API orchestrating gateway redirection and callback verification.
    """

    @action(detail=False, methods=["post"], url_path="initiate", permission_classes=[permissions.IsAuthenticated])
    def initiate(self, request):
        """
        Requests a payment token/Authority from the gateway for an unpaid order.
        """
        serializer = InitiatePaymentInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        callback_url = serializer.validated_data["callback_url"]
        gateway = serializer.validated_data.get("gateway", "zarinpal")

        try:
            order = Order.objects.get(id=order_id, buyer=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "سفارش مورد نظر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = PaymentService.initiate_payment(
                order=order,
                callback_url=callback_url,
                gateway=gateway,
            )
            return Response(result, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get", "post"], url_path="verify", permission_classes=[permissions.AllowAny])
    def verify(self, request):
        """
        Webhook / callback verification endpoint called upon customer return from bank.
        """
        # Bank may send params via GET (Zarinpal query params) or POST
        data = request.data if request.method == "POST" else request.query_params
        serializer = VerifyPaymentInputSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        authority = serializer.validated_data["authority"]
        status_param = serializer.validated_data.get("status", "OK")

        try:
            result = PaymentService.verify_payment(
                authority=authority,
                status_param=status_param,
            )
            return Response(result, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message, "success": False}, status=status.HTTP_400_BAD_REQUEST)
