from rest_framework import serializers
from ..models.order import Order, OrderShipment, OrderItem, OrderStatusHistory, ShipmentStatusHistory
from .base import BaseModelSerializer, BaseInputSerializer
from .location import AddressSerializer
from .catalog import ItemListSerializer


class OrderItemSerializer(BaseModelSerializer):
    item = ItemListSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "item", "quantity", "unit_price", "discount_amount", "total_price"]

    def get_total_price(self, obj):
        return (obj.unit_price - obj.discount_amount) * obj.quantity


class OrderShipmentSerializer(BaseModelSerializer):
    seller_name = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = OrderShipment
        fields = [
            "id",
            "seller",
            "seller_name",
            "shipping_cost",
            "shipping_method",
            "tracking_code",
            "status",
            "shipped_at",
            "delivered_at",
            "items",
        ]

    def get_seller_name(self, obj):
        return obj.seller.get_full_name() or obj.seller.phone


class OrderStatusHistorySerializer(BaseModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.get_full_name", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ["id", "from_status", "to_status", "note", "changed_by_name", "created_at"]


class OrderListSerializer(BaseModelSerializer):
    shipments_count = serializers.IntegerField(source="shipments.count", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "payment_status",
            "total_items_amount",
            "total_shipping_cost",
            "discount_amount",
            "payable_amount",
            "shipments_count",
            "created_at",
        ]


class OrderDetailSerializer(OrderListSerializer):
    shipping_address = AddressSerializer(read_only=True)
    shipments = OrderShipmentSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + [
            "shipping_address",
            "shipments",
            "status_history",
        ]


class CheckoutInputSerializer(BaseInputSerializer):
    shipping_address_id = serializers.IntegerField(required=False, allow_null=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=50)
