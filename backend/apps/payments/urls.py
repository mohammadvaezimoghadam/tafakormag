from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentCallbackView,
    PaymentTransactionViewSet,
    PaymentVerifyView,
)

app_name = "payments"

router = DefaultRouter()
router.register(r"transactions", PaymentTransactionViewSet, basename="payment-transaction")

urlpatterns = [
    path("callback/", PaymentCallbackView.as_view(), name="payment-callback"),
    path("verify/", PaymentVerifyView.as_view(), name="payment-verify"),
    path("", include(router.urls)),
]

