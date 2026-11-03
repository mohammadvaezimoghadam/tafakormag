from django.urls import path
from .views import (
    SubscriptionPlanListView,
    PurchaseVerifyView,
    UserSubscriptionStatusView,
)

urlpatterns = [
    # دریافت لیست پلن‌ها و قیمت‌ها: GET /api/subscriptions/plans/?plugin=quran
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),

    # وریفای خرید کافه‌بازار و فعال‌سازی اشتراک: POST /api/subscriptions/verify/
    path('verify/', PurchaseVerifyView.as_view(), name='purchase-verify'),

    # استعلام وضعیت اشتراک کاربر جاری: GET /api/subscriptions/my-status/?plugin=quran
    path('my-status/', UserSubscriptionStatusView.as_view(), name='my-status'),
]
