from rest_framework import serializers
from decimal import Decimal
from ..models.cart import Cart, CartItem
from .base import BaseModelSerializer, BaseInputSerializer
from .catalog import ItemListSerializer


class CartItemSerializer(BaseModelSerializer):
    item = ItemListSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "item", "quantity", "line_total", "created_at"]

    def get_line_total(self, obj) -> Decimal:
        unit_price = obj.item.discount_price if obj.item.discount_price else obj.item.price
        return unit_price * obj.quantity


class AddToCartInputSerializer(BaseInputSerializer):
    item_id = serializers.IntegerField(min_value=1, required=True)
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartQuantityInputSerializer(BaseInputSerializer):
    quantity = serializers.IntegerField(min_value=0, required=True)


class CartSummarySerializer(BaseInputSerializer):
    """
    Serializer representing the output of CartService.get_cart_summary
    """
    cart_id = serializers.IntegerField()
    total_items_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=0)
    has_physical_items = serializers.BooleanField()
    has_digital_items = serializers.BooleanField()
    items = serializers.ListField(child=serializers.DictField())
