import uuid
import base64

from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

import requests
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)
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
            # اگر ارسال پیامک با خطا مواجه شد، باز هم کد را در کش ذخیره کرده و به کانال بله سوئیچ می‌کنیم
            cache.set(cache_key, otp, timeout=120)
            channel = "bale"
            sent_via_kavenegar = False

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
        force = request.data.get('force', False)
        
        if platform not in ['telegram', 'bale']:
            return Response({"error": "پلتفرم نامعتبر."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not token:
            # در صورتی که کاربر بخواهد توکن را حذف کند (قطع اتصال)
            old_token = request.user.telegram_bot_token if platform == 'telegram' else request.user.bale_bot_token
            chat_id = request.user.telegram_chat_id if platform == 'telegram' else request.user.bale_chat_id
            
            if old_token and chat_id:
                try:
                    if platform == 'telegram':
                        telegram_base = settings.TELEGRAM_API_URL.rstrip('/')
                        send_url = f"{telegram_base}{old_token}/sendMessage"
                    else:
                        send_url = f"https://tapi.bale.ai/bot{old_token}/sendMessage"
                    
                    msg_text = (
                        f"🔌 <b>قطع اتصال ربات اختصاصی تفکر</b>\n\n"
                        f"اتصال ربات تفکر شما با موفقیت از سیستم تفکر قطع شد."
                    )
                    requests.post(send_url, json={
                        "chat_id": int(chat_id),
                        "text": msg_text,
                        "parse_mode": "HTML"
                    }, timeout=5)
                except Exception as send_err:
                    logger.error(f"Failed to send disconnect message to owner: {send_err}")

            if old_token:
                try:
                    if platform == 'telegram':
                        telegram_base = settings.TELEGRAM_API_URL.rstrip('/')
                        url = f"{telegram_base}{old_token}/setWebhook?url=https://yourdomain.com/dummy-deleted-webhook"
                    else:
                        url = f"https://tapi.bale.ai/bot{old_token}/setWebhook?url=https://yourdomain.com/dummy-deleted-webhook"
                    requests.get(url, timeout=5)
                except Exception as e:
                    logger.error(f"Failed to set dummy webhook during bot disconnect: {e}")

            if platform == 'telegram':
                request.user.telegram_bot_token = None
                request.user.telegram_bot_username = None
                request.user.telegram_bot_disconnect_reason = None
            else:
                request.user.bale_bot_token = None
                request.user.bale_bot_username = None
                request.user.bale_bot_disconnect_reason = None
            request.user.save()
            return Response({"success": True, "message": "ربات با موفقیت حذف شد."})

        # اعتبارسنجی توکن از طریق متد getMe پیام‌رسان مربوطه
        try:
            if token.startswith("mock_"):
                is_valid = True
                username = f"@{token}_bot"
            else:
                if platform == 'telegram':
                    # استفاده از TELEGRAM_API_URL برای عبور از پروکسی (در صورت اجرا روی سرور ایران)
                    # فرمت صحیح: /botTOKEN/getMe (بدون / بین bot و توکن)
                    telegram_base = settings.TELEGRAM_API_URL.rstrip('/')
                    url = f"{telegram_base}{token}/getMe"
                else:
                    url = f"https://tapi.bale.ai/bot{token}/getMe"
                    
                res = requests.get(url, timeout=25)
                is_valid = (res.status_code == 200)
                if is_valid:
                    bot_data = res.json().get('result', {})
                    username = f"@{bot_data.get('username')}"

            if is_valid:
                
                if platform == 'telegram':
                    others = User.objects.filter(telegram_bot_token=token).exclude(pk=request.user.pk)
                    if others.exists() and not force:
                        return Response({
                            "error": "این ربات در حال حاضر به حساب کاربری دیگری متصل است. آیا مایلید مالکیت آن را به این حساب انتقال دهید؟",
                            "code": "claimed_by_another_user",
                            "other_phone": others.first().phone
                        }, status=status.HTTP_400_BAD_REQUEST)

                    for other_user in others:
                        if other_user.telegram_chat_id:
                            telegram_base = settings.TELEGRAM_API_URL.rstrip('/')
                            notify_url = f"{telegram_base}{token}/sendMessage"
                            msg_text = (
                                "⚠️ <b>اتصال ربات اختصاصی شما قطع شد!</b>\n\n"
                                f"توکن این ربات به حساب کاربری دیگری با شماره تلفن <code>{request.user.phone}</code> اختصاص یافت. "
                                "کانال‌ها و گروه‌های ثبت شده شما حفظ شده‌اند اما برای ارسال‌های بعدی باید ربات جدیدی ثبت کنید."
                            )
                            try:
                                requests.post(notify_url, json={"chat_id": other_user.telegram_chat_id, "text": msg_text, "parse_mode": "HTML"}, timeout=10)
                            except Exception as e:
                                logger.error(f"Failed to send telegram disconnect notice: {e}")
                        other_user.telegram_bot_token = None
                        other_user.telegram_bot_username = None
                        other_user.telegram_bot_disconnect_reason = 'claimed_by_another_user'
                        other_user.save()
                    request.user.telegram_bot_token = token
                    request.user.telegram_bot_username = username
                    request.user.telegram_bot_disconnect_reason = None
                else:
                    others = User.objects.filter(bale_bot_token=token).exclude(pk=request.user.pk)
                    if others.exists() and not force:
                        return Response({
                            "error": "این ربات در حال حاضر به حساب کاربری دیگری متصل است. آیا مایلید مالکیت آن را به این حساب انتقال دهید؟",
                            "code": "claimed_by_another_user",
                            "other_phone": others.first().phone
                        }, status=status.HTTP_400_BAD_REQUEST)

                    for other_user in others:
                        if other_user.bale_chat_id:
                            notify_url = f"https://tapi.bale.ai/bot{token}/sendMessage"
                            msg_text = (
                                "⚠️ <b>اتصال ربات اختصاصی شما قطع شد!</b>\n\n"
                                f"توکن این ربات به حساب کاربری دیگری با شماره تلفن <code>{request.user.phone}</code> اختصاص یافت. "
                                "کانال‌ها و گروه‌های ثبت شده شما حفظ شده‌اند اما برای ارسال‌های بعدی باید ربات جدیدی ثبت کنید."
                            )
                            try:
                                requests.post(notify_url, json={"chat_id": other_user.bale_chat_id, "text": msg_text, "parse_mode": "HTML"}, timeout=10)
                            except Exception as e:
                                logger.error(f"Failed to send bale disconnect notice: {e}")
                        other_user.bale_bot_token = None
                        other_user.bale_bot_username = None
                        other_user.bale_bot_disconnect_reason = 'claimed_by_another_user'
                        other_user.save()
                    request.user.bale_bot_token = token
                    request.user.bale_bot_username = username
                    request.user.bale_bot_disconnect_reason = None
                
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

    # ۴.۵ - اعتبارسنجی آنی توکن ربات اختصاصی
    @action(methods=['post'], detail=False, url_path='validate-custom-bot',
            permission_classes=[permissions.IsAuthenticated])
    def validate_custom_bot(self, request):
        platform = request.data.get('platform')
        token = request.data.get('token', '').strip()
        
        if platform not in ['telegram', 'bale'] or not token:
            return Response({"error": "پلتفرم و توکن الزامی هستند."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            if token.startswith("mock_"):
                return Response({
                    "valid": True,
                    "username": f"@{token}_bot",
                    "name": f"Mock Bot ({platform})",
                    "avatar": None
                })

            if platform == 'telegram':
                telegram_base = settings.TELEGRAM_API_URL.rstrip('/')
                url = f"{telegram_base}{token}/getMe"
            else:
                url = f"https://tapi.bale.ai/bot{token}/getMe"
                
            res = requests.get(url, timeout=15)
            if res.status_code != 200:
                return Response({"valid": False, "error": "توکن نامعتبر است یا مشکلی در اتصال وجود دارد."}, status=status.HTTP_400_BAD_REQUEST)
                
            bot_data = res.json().get('result', {})
            bot_id = bot_data.get('id')
            username = f"@{bot_data.get('username')}"
            first_name = bot_data.get('first_name')
            
            avatar_base64 = None
            
            if platform == 'telegram' and bot_id:
                try:
                    photos_url = f"{telegram_base}{token}/getUserProfilePhotos"
                    photos_res = requests.get(photos_url, params={"user_id": bot_id, "limit": 1}, timeout=5)
                    if photos_res.status_code == 200:
                        photos_data = photos_res.json().get('result', {})
                        photos = photos_data.get('photos', [])
                        if photos and len(photos) > 0 and len(photos[0]) > 0:
                            smallest_photo = photos[0][0] # take smallest size
                            file_id = smallest_photo.get('file_id')
                            
                            file_url = f"{telegram_base}{token}/getFile"
                            file_res = requests.get(file_url, params={"file_id": file_id}, timeout=5)
                            if file_res.status_code == 200:
                                file_path = file_res.json().get('result', {}).get('file_path')
                                if file_path:
                                    if "api.telegram.org" in telegram_base:
                                        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                                    else:
                                        download_url = telegram_base.replace("/bot", "/file/bot") + f"/{file_path}"
                                    
                                    img_res = requests.get(download_url, timeout=10)
                                    if img_res.status_code == 200:
                                        encoded_img = base64.b64encode(img_res.content).decode('utf-8')
                                        avatar_base64 = f"data:image/jpeg;base64,{encoded_img}"
                except Exception as photo_err:
                    logger.warning(f"Failed to fetch bot profile photo: {photo_err}")
                    
            return Response({
                "valid": True,
                "username": username,
                "name": first_name,
                "avatar": avatar_base64
            })
        except Exception as e:
            return Response({"valid": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                    "token": u.telegram_bot_token,
                    "owner_chat_id": u.telegram_chat_id
                })
            if u.bale_bot_token:
                data.append({
                    "user_id": u.id,
                    "phone": u.phone,
                    "platform": "bale",
                    "token": u.bale_bot_token,
                    "owner_chat_id": u.bale_chat_id
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