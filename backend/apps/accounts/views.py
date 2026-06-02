import uuid

from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

import requests
from django.db.models import Q
from otp.dispatcher import send_sms_otp, OTPDeliveryError
from .models import User, BotConnectionToken, MessagingTarget
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
            # منحصراً تلاش برای ارسال پیامک
            channel = send_sms_otp(phone, otp)
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

    # ۳ - دریافت توکن اتصال به ربات‌ها (برای ربات عمومی OTP بله)
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

    # ۴ - به‌روزرسانی ربات اختصاصی کاربر
    @action(methods=['post'], detail=False, url_path='update-custom-bot',
            permission_classes=[permissions.IsAuthenticated])
    def update_custom_bot(self, request):
        platform = request.data.get('platform')
        token = request.data.get('token', '').strip()
        
        if platform not in ['telegram', 'bale']:
            return Response({"error": "پلتفرم نامعتبر."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not token:
            # در صورتی که کاربر بخواهد توکن را حذف کند (قطع اتصال)
            if platform == 'telegram':
                request.user.telegram_bot_token = None
                request.user.telegram_bot_username = None
            else:
                request.user.bale_bot_token = None
                request.user.bale_bot_username = None
            request.user.save()
            return Response({"success": True, "message": "ربات با موفقیت حذف شد."})

        # اعتبارسنجی توکن از طریق متد getMe پیام‌رسان مربوطه
        try:
            if platform == 'telegram':
                url = f"https://api.telegram.org/bot{token}/getMe"
            else:
                url = f"https://tapi.bale.ai/bot{token}/getMe"
                
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                bot_data = res.json().get('result', {})
                username = f"@{bot_data.get('username')}"
                
                if platform == 'telegram':
                    request.user.telegram_bot_token = token
                    request.user.telegram_bot_username = username
                else:
                    request.user.bale_bot_token = token
                    request.user.bale_bot_username = username
                
                request.user.save()
                return Response({
                    "success": True, 
                    "username": username,
                    "message": "ربات با موفقیت متصل و ثبت شد."
                })
            else:
                return Response({"error": "توکن نامعتبر است. لطفاً توکن دریافتی از BotFather را بررسی کنید."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "خطا در برقراری ارتباط با سرور پیام‌رسان."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ۵ - دریافت لیست ربات‌های اختصاصی فعال (برای ربات‌رانر)
    @action(methods=['get'], detail=False, url_path='active-tokens')
    def active_tokens(self, request):
        # بررسی کلید امنیتی بات
        api_key = request.headers.get("X-Bot-Service-Key")
        if not api_key or api_key != settings.BOT_API_KEY:
            return Response({"error": "غیر مجاز"}, status=status.HTTP_403_FORBIDDEN)
            
        # فیلتر کردن کاربرانی که حداقل یکی از توکن‌ها را پر کرده‌اند
        users = User.objects.filter(
            Q(telegram_bot_token__isnull=False) | Q(bale_bot_token__isnull=False)
        )
        data = []
        for u in users:
            if u.telegram_bot_token:
                data.append({
                    "user_id": u.id,
                    "phone": u.phone,
                    "platform": "telegram",
                    "token": u.telegram_bot_token
                })
            if u.bale_bot_token:
                data.append({
                    "user_id": u.id,
                    "phone": u.phone,
                    "platform": "bale",
                    "token": u.bale_bot_token
                })
        return Response(data)

    # ۶ - دریافت و ویرایش اطلاعات پروفایل جاری کاربر
    @action(methods=['get', 'patch', 'put'], detail=False, url_path='profile',
            permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        if request.method in ['PATCH', 'PUT']:
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(UserSerializer(request.user).data)

    # ۷ - دریافت لیست مقاصد ارتباطی کاربر (برای مدیریت چک‌باکس‌های اتصالات در تاپیک)
    @action(methods=['get', 'post'], detail=False, url_path='destinations',
            permission_classes=[permissions.IsAuthenticated])
    def destinations(self, request):
        if request.method == 'POST':
            platform = request.data.get('platform')
            chat_id = str(request.data.get('chat_id', '')).strip()
            label = request.data.get('label', '').strip()
            
            if platform not in ['telegram', 'bale'] or not chat_id or not label:
                return Response({"error": "پلتفرم، شناسه چت و برچسب الزامی هستند."}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                target, created = MessagingTarget.objects.update_or_create(
                    user=request.user,
                    platform=platform,
                    chat_id=chat_id,
                    defaults={'label': label, 'is_active': True}
                )
                return Response({
                    "id": target.id,
                    "platform": target.platform,
                    "chat_id": target.chat_id,
                    "label": target.label,
                    "is_active": target.is_active
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": f"خطا در ثبت مقصد دستی: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        platform = request.query_params.get('platform')
        queryset = MessagingTarget.objects.filter(user=request.user)
        if platform in ['telegram', 'bale']:
            queryset = queryset.filter(platform=platform)
        
        data = [
            {
                "id": t.id,
                "platform": t.platform,
                "chat_id": t.chat_id,
                "label": t.label,
                "is_active": t.is_active
            }
            for t in queryset
        ]
        return Response(data)

    @action(methods=['post'], detail=False, url_path='delete-user-destination',
            permission_classes=[permissions.IsAuthenticated])
    def delete_user_destination(self, request):
        dest_id = request.data.get('destination_id')
        if not dest_id:
            return Response({"error": "شناسه مقصد الزامی است."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target = MessagingTarget.objects.get(pk=dest_id, user=request.user)
            target.delete()
            return Response({"success": True})
        except MessagingTarget.DoesNotExist:
            return Response({"error": "مقصد یافت نشد."}, status=status.HTTP_404_NOT_FOUND)