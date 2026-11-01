from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..services.cart_service import CartService
from ..serializers.cart import (
    AddToCartInputSerializer,
    UpdateCartQuantityInputSerializer,
    CartSummarySerializer,
)
from ..exceptions import MarketplaceError


class CartViewSet(viewsets.ViewSet):
    """
    Shopping Cart API orchestrating client cart additions, updates, and subtotals.
    All actions delegate strictly to CartService to maintain business logic integrity.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        Retrieves the full active cart summary including items, prices, and shipping metadata.
        """
        summary = CartService.get_cart_summary(request.user)
        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        """
        Adds a product to the user's cart or increments quantity.
        """
        serializer = AddToCartInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        item_id = serializer.validated_data["item_id"]
        quantity = serializer.validated_data.get("quantity", 1)

        try:
            CartService.add_item(
                user=request.user,
                item_id=item_id,
                quantity=quantity
            )
            # Return updated cart summary
            summary = CartService.get_cart_summary(request.user)
            return Response(summary, status=status.HTTP_201_CREATED)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="quantity")
    def update_quantity(self, request, pk=None):
        """
        Updates the quantity of a specific cart item. If 0, removes the item.
        """
        serializer = UpdateCartQuantityInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data["quantity"]

        try:
            CartService.update_quantity(
                user=request.user,
                cart_item_id=int(pk),
                quantity=quantity
            )
            summary = CartService.get_cart_summary(request.user)
            return Response(summary, status=status.HTTP_200_OK)
        except MarketplaceError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"], url_path="remove")
    def remove_item(self, request, pk=None):
        """
        Deletes a specific item from the shopping cart.
        """
        success = CartService.remove_item(user=request.user, cart_item_id=int(pk))
        if not success:
            return Response({"detail": "آیتم در سبد خرید یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        summary = CartService.get_cart_summary(request.user)
        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="clear")
    def clear(self, request):
        """
        Clears all items from the current user's shopping cart.
        """
        CartService.clear_cart(request.user)
        summary = CartService.get_cart_summary(request.user)
        return Response(summary, status=status.HTTP_200_OK)
