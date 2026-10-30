from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F, Prefetch
from decimal import Decimal

from ..models.catalog import Category, Item, ItemImage
from ..serializers.catalog import (
    CategorySerializer,
    ItemListSerializer,
    ItemDetailSerializer,
    ItemCreateUpdateSerializer,
)
from ..permissions import IsOwnerOrReadOnly


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public catalog hierarchy endpoint providing nested parent/child categories.
    """
    queryset = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related(
        Prefetch("children", queryset=Category.objects.filter(is_active=True))
    )
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ItemViewSet(viewsets.ModelViewSet):
    """
    Comprehensive Catalog API for book and marketplace items:
    - Public listing, full-text search, and multi-faceted filtering.
    - Deep details with book metadata (author, publisher, ISBN).
    - Authenticated seller creation, updates, and soft deletion.
    """

    def get_permissions(self):
        if self.action in ["list", "retrieve", "record_view"]:
            return [permissions.AllowAny()]
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ItemDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ItemCreateUpdateSerializer
        return ItemListSerializer

    def get_queryset(self):
        # Base query optimized for performance with zero N+1 lookups
        qs = (
            Item.objects.select_related(
                "seller",
                "category",
                "city",
                "city__province",
                "book_detail",
            )
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ItemImage.objects.filter(is_cover=True),
                    to_attr="cover_images"
                )
            )
        )

        # For regular public catalog browsing, show only AVAILABLE items
        if self.action not in ["my_items"]:
            qs = qs.filter(status=Item.Status.AVAILABLE)

        # 1. Search Query (Title, Description, Author, Publisher, ISBN)
        q = self.request.query_params.get("search", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(book_detail__author__icontains=q)
                | Q(book_detail__publisher__icontains=q)
                | Q(book_detail__isbn__icontains=q)
            )

        # 2. Filter by Category (with parent-child hierarchy support)
        category_param = self.request.query_params.get("category")
        if category_param:
            try:
                if category_param.isdigit():
                    cat = Category.objects.filter(id=int(category_param)).first()
                else:
                    cat = Category.objects.filter(slug=category_param).first()
                if cat:
                    child_ids = list(cat.children.values_list("id", flat=True))
                    qs = qs.filter(category_id__in=[cat.id] + child_ids)
                else:
                    qs = qs.none()
            except Exception:
                pass

        # 3. Filter by Deal Type (sale vs donation)
        deal_type = self.request.query_params.get("deal_type")
        if deal_type in [Item.DealType.SALE, Item.DealType.DONATION]:
            qs = qs.filter(deal_type=deal_type)

        # 4. Filter by Delivery Type (physical vs digital)
        delivery_type = self.request.query_params.get("delivery_type")
        if delivery_type in [Item.DeliveryType.PHYSICAL, Item.DeliveryType.DIGITAL]:
            qs = qs.filter(delivery_type=delivery_type)

        # 5. Filter by In-Stock Only
        in_stock = self.request.query_params.get("in_stock")
        if in_stock in ["1", "true", "True"]:
            qs = qs.filter(Q(stock__gt=0) | Q(is_unlimited_stock=True))

        # 6. Filter by Has Discount
        has_discount = self.request.query_params.get("has_discount")
        if has_discount in ["1", "true", "True"]:
            qs = qs.filter(discount_price__isnull=False, discount_price__gt=0)

        # 7. Filter by Condition
        condition = self.request.query_params.get("condition")
        if condition:
            qs = qs.filter(condition=condition)

        # 8. Filter by Specific Book Metadata (Author, Publisher, ISBN)
        author = self.request.query_params.get("author")
        if author:
            qs = qs.filter(book_detail__author__icontains=author.strip())

        publisher = self.request.query_params.get("publisher")
        if publisher:
            qs = qs.filter(book_detail__publisher__icontains=publisher.strip())

        isbn = self.request.query_params.get("isbn")
        if isbn:
            qs = qs.filter(book_detail__isbn__iexact=isbn.strip())

        # 9. Price Range Filters
        min_price = self.request.query_params.get("min_price")
        if min_price and min_price.isdigit():
            qs = qs.filter(price__gte=Decimal(min_price))

        max_price = self.request.query_params.get("max_price")
        if max_price and max_price.isdigit():
            qs = qs.filter(price__lte=Decimal(max_price))

        # 10. Featured Items Filter
        is_featured = self.request.query_params.get("featured")
        if is_featured in ["1", "true", "True"]:
            qs = qs.filter(is_featured=True)

        # 11. Topic Integration Filter
        topic_id = self.request.query_params.get("topic_id")
        if topic_id and topic_id.isdigit():
            qs = qs.filter(topic_id=int(topic_id))

        # 12. Dynamic Ordering with standard aliases
        ordering = self.request.query_params.get("ordering", "newest")
        ordering_map = {
            "newest": "-created_at",
            "cheapest": "price",
            "price_asc": "price",
            "most_expensive": "-price",
            "price_desc": "-price",
            "popular": "-views_count",
            "most_viewed": "-views_count",
            "-created_at": "-created_at",
            "created_at": "created_at",
            "price": "price",
            "-price": "-price",
            "views_count": "views_count",
            "-views_count": "-views_count",
        }
        qs = qs.order_by(ordering_map.get(ordering, "-created_at"))

        return qs

    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def record_view(self, request, pk=None):
        """
        Atomically increments the view counter for an item.
        """
        item = self.get_object()
        Item.objects.filter(id=item.id).update(views_count=F("views_count") + 1)
        return Response({"status": "view recorded"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_items(self, request):
        """
        Returns all items published by the authenticated seller across all statuses (draft, available, completed).
        """
        qs = (
            Item.objects.filter(seller=request.user)
            .select_related("category", "book_detail")
            .order_by("-created_at")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ItemListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = ItemListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)
