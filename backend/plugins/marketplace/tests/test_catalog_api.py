from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from ..models.catalog import Category, Item, BookDetail

User = get_user_model()


class CatalogAndCartAPITests(TestCase):
    """
    Automated integration tests for REST API endpoints and permissions.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="09121111111", password="password123")
        self.seller = User.objects.create_user(phone="09122222222", password="password123")

        self.category = Category.objects.create(name="شعر و ادب", slug="poetry")

        # Book with full detail
        self.item = Item.objects.create(
            seller=self.seller,
            category=self.category,
            title="گلستان سعدی",
            slug="golestan-saadi",
            price=Decimal("120000"),
            stock=10,
            status=Item.Status.AVAILABLE,
        )
        BookDetail.objects.create(
            item=self.item,
            author="سعدی شیرازی",
            publisher="انتشارات صبا",
            isbn="978-964-001-001-1",
        )

    def test_public_catalog_list_200(self):
        """Public catalog listing is accessible without authentication."""
        response = self.client.get("/api/v1/marketplace/items/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "گلستان سعدی")

    def test_search_by_author_filter(self):
        """Searching catalog by author returns specific matches."""
        response = self.client.get("/api/v1/marketplace/items/?author=سعدی")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "گلستان سعدی")

        # Search for non-existent author returns empty list
        response_empty = self.client.get("/api/v1/marketplace/items/?author=فردوسی")
        self.assertEqual(len(response_empty.json()), 0)

    def test_unauthenticated_cart_access_401(self):
        """Anonymous access to private cart endpoint is blocked with 401."""
        response = self.client.get("/api/v1/marketplace/cart/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_add_to_cart_api_201(self):
        """Authenticated user successfully adds an item via the REST API."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v1/marketplace/cart/items/", {
            "item_id": self.item.id,
            "quantity": 2,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["total_items_count"], 2)
        self.assertEqual(Decimal(str(data["subtotal"])), Decimal("240000"))
