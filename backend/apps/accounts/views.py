import uuid

from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from otp_dispatcher.dispatcher import send_otp, OTPDeliveryError
from .models import User, BotConnectionToken
from .serializers import (
    ConnectTokenResponseSerializer,
    RequestOTPSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)

class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer

    # ۱ - درخواست کد
    @action(methods=['post'], detail=False, url_path='request-otp')
    def request_otp(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        force_sms = serializer.validated_data.get('force_sms', False)

        cache_key = f"otp_{phone}"
        existing_otp = cache.get(cache_key)

        # در صورتی که درخواست پیامک اجباری باشد (bypass limit)، برای راحتی کاربر زمان‌بندی کش مجدد را نادیده می‌گیریم یا تایید می‌کنیم
        if existing_otp and not force_sms:
            if settings.DEBUG:
                print(f"\n📱 OTP قبلاً برای {phone} ارسال شده است: {existing_otp}\n")
            return Response(
                {"error": "کد تأیید قبلاً ارسال شده است. لطفاً ۲ دقیقه صبر کنید."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        otp = str(uuid.uuid4().int)[:4]

        try:
            channel = send_otp(phone, otp, force_sms=force_sms)
            cache.set(cache_key, otp, timeout=120)
            sent_via_kavenegar = (channel == "sms")
        except OTPDeliveryError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            "message": "کد تأیید ارسال شد.",
            "channel": channel,
            "otp": otp if settings.DEBUG and not sent_via_kavenegar else None,
        })

    # ۲ - تأیید کد و ورود
    @action(methods=['post'], detail=False, url_path='verify-otp')
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        otp = serializer.validated_data['otp']

        cache_key = f"otp_{phone}"
        stored_otp = cache.get(cache_key)

        if stored_otp is None:
            return Response(
                {"error": "کد تأیید منقضی شده است. لطفاً دوباره درخواست کنید."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if stored_otp != otp:
            return Response(
                {"error": "کد تأیید نادرست است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache.delete(cache_key)

        user, created = User.objects.get_or_create(phone=phone)
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": UserSerializer(user).data
        })

    # ۳ - دریافت توکن اتصال به ربات‌ها
    @action(methods=['get'], detail=False, url_path='connect-token',
            permission_classes=[permissions.IsAuthenticated])
    def connect_token(self, request):
        platform = request.query_params.get('platform')
        if platform not in ['telegram', 'bale']:
            return Response({"error": "پلتفرم نامعتبر."}, status=status.HTTP_400_BAD_REQUEST)

        BotConnectionToken.objects.filter(
            user=request.user,
            platform=platform,
            is_used=False
        ).update(is_used=True)

        token = BotConnectionToken.objects.create(
            user=request.user,
            platform=platform
        )
        return Response(ConnectTokenResponseSerializer(token).data)