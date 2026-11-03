import math
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone

from .models import SubscriptionPlan
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionStatusSerializer,
    PurchaseVerifyRequestSerializer,
)
from .services import SubscriptionService
from .utils import get_user_active_subscription, has_active_subscription


class SubscriptionPlanListView(generics.ListAPIView):
    """
    دریافت لیست طرح‌ها و پلن‌های فعال اشتراک.
    پشتیبانی از فیلتر بر اساس شناسه افزونه: ?plugin=quran
    قابل استفاده برای تمام کاربران (حتی کاربران مهمان جهت مشاهده قیمت‌ها).
    """
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = SubscriptionPlan.objects.filter(is_active=True)
        plugin = self.request.query_params.get('plugin')
        if plugin:
            qs = qs.filter(plugin_identifier__in=[plugin, 'all'])
        return qs.order_by('duration_days', 'price')


class PurchaseVerifyView(APIView):
    """
    اعتبارسنجی رسمی خرید کاربر در کافه‌بازار و فعال‌سازی/تمدید اشتراک.
    نیازمند لاگین بودن کاربر (IsAuthenticated).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PurchaseVerifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku = serializer.validated_data['sku']
        purchase_token = serializer.validated_data['purchase_token']
        marketplace = serializer.validated_data.get('marketplace', 'cafebazaar')
        package_name = serializer.validated_data.get('package_name')

        user_sub, log_entry = SubscriptionService.verify_and_activate(
            user=request.user,
            sku=sku,
            purchase_token=purchase_token,
            marketplace=marketplace,
            package_name=package_name
        )

        now = timezone.now()
        remaining_days = max(0, math.ceil((user_sub.expires_at - now).total_seconds() / 86400))

        status_data = {
            'has_active_subscription': user_sub.is_currently_valid,
            'plugin_identifier': user_sub.plugin_identifier,
            'status': user_sub.status,
            'expires_at': user_sub.expires_at,
            'remaining_days': remaining_days,
            'plan_title': user_sub.plan.title if user_sub.plan else None,
            'sku': user_sub.plan.sku if user_sub.plan else sku,
        }

        return Response({
            'success': True,
            'message': 'اشتراک شما با موفقیت تایید و فعال گردید.',
            'subscription': status_data,
            'verified_at': log_entry.created_at,
        }, status=status.HTTP_200_OK)


class UserSubscriptionStatusView(APIView):
    """
    استعلام وضعیت فعلی اشتراک کاربر در یک افزونه معین:
    GET /api/subscriptions/my-status/?plugin=quran
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        plugin = self.request.query_params.get('plugin', 'quran')
        active_sub = get_user_active_subscription(request.user, plugin)

        now = timezone.now()
        if active_sub:
            remaining_days = max(0, math.ceil((active_sub.expires_at - now).total_seconds() / 86400))
            status_data = {
                'has_active_subscription': True,
                'plugin_identifier': plugin,
                'status': active_sub.status,
                'expires_at': active_sub.expires_at,
                'remaining_days': remaining_days,
                'plan_title': active_sub.plan.title if active_sub.plan else None,
                'sku': active_sub.plan.sku if active_sub.plan else None,
            }
        else:
            status_data = {
                'has_active_subscription': False,
                'plugin_identifier': plugin,
                'status': 'none',
                'expires_at': None,
                'remaining_days': 0,
                'plan_title': None,
                'sku': None,
            }

        serializer = UserSubscriptionStatusSerializer(data=status_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
