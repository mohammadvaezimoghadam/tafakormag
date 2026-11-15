from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ItemViewSet,
    CartViewSet,
    OrderViewSet,
    PaymentViewSet,
    DonationRequestViewSet,
    DonationViewSet,
    ProvinceViewSet,
    CityViewSet,
    AddressViewSet,
    ReviewViewSet,
    WishlistViewSet,
    DigitalAccessViewSet,
    BookTitleViewSet,
    BookStationViewSet,
    PhysicalCopyViewSet,
    BadgeViewSet,
    UserShelfBookViewSet,
)

app_name = "marketplace"

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"items", ItemViewSet, basename="item")
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"donation-requests", DonationRequestViewSet, basename="donation-request")
router.register(r"donations", DonationViewSet, basename="donation")
router.register(r"provinces", ProvinceViewSet, basename="province")
router.register(r"cities", CityViewSet, basename="city")
router.register(r"addresses", AddressViewSet, basename="address")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"wishlist", WishlistViewSet, basename="wishlist")
router.register(r"digital-library", DigitalAccessViewSet, basename="digital-library")
router.register(r"book-titles", BookTitleViewSet, basename="book-title")
router.register(r"book-stations", BookStationViewSet, basename="book-station")
router.register(r"copies", PhysicalCopyViewSet, basename="copy")
router.register(r"badges", BadgeViewSet, basename="badge")
router.register(r"shelf", UserShelfBookViewSet, basename="shelf")

urlpatterns = [
    path("", include(router.urls)),
]
