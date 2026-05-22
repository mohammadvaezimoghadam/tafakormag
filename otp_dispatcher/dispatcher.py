import logging
import requests
from django.conf import settings
from apps.accounts.models import User
from apps.accounts.services import send_otp_sms, SMSDeliveryError, kavenegar_configured

logger = logging.getLogger(__name__)


class OTPDeliveryError(Exception):
    """خطا در ارسال کد تایید از تمامی درگاه‌ها."""
    pass


def send_otp(phone: str, otp: str) -> str:
    """
    ارسال کد تایید به کاربر.
    ابتدا تلاش می‌کند از طریق ربات‌های پیام‌رسان (بله و تلگرام) ارسال کند.
    در صورت عدم امکان یا خطا، از طریق پیامک کاوه‌نگار ارسال می‌کند.
    
    برمی‌گرداند: روش ارسال شده ('bale', 'telegram', 'sms', 'debug')
    """
    user = User.objects.filter(phone=phone).first()

    # ۱. تلاش برای ارسال از طریق پیام‌رسان بله
    if user and user.bale_chat_id:
        bale_token = (getattr(settings, "BALE_BOT_TOKEN", None) or "").strip()
        if bale_token:
            url = f"https://api.bale.ai/bot{bale_token}/sendMessage"
            text = f"به تفکر خوش آمدید، بفرمایید کد ورود : {otp}"
            try:
                res = requests.post(url, json={
                    "chat_id": user.bale_chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }, timeout=5)
                if res.status_code == 200:
                    logger.info(f"OTP successfully sent via Bale bot to user {phone}")
                    return "bale"
                else:
                    logger.warning(f"Bale bot API returned status {res.status_code} for user {phone}: {res.text}")
            except Exception as e:
                logger.exception(f"Failed to send OTP via Bale bot to user {phone}")

    # ۲. تلاش برای ارسال از طریق پیام‌رسان تلگرام
    if user and user.telegram_chat_id:
        telegram_token = (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip()
        if telegram_token:
            # بررسی پروکسی تلگرام
            proxy_url = (getattr(settings, "TELEGRAM_PROXY_URL", None) or "").strip()
            proxies = {"https": proxy_url} if proxy_url else None

            telegram_api_url = (getattr(settings, "TELEGRAM_API_URL", None) or "https://api.telegram.org/bot").strip()
            if not telegram_api_url.endswith("/"):
                telegram_api_url += "/"
            url = f"{telegram_api_url}{telegram_token}/sendMessage"
            text = f"به تفکر خوش آمدید، بفرمایید کد ورود : {otp}"
            try:
                res = requests.post(url, json={
                    "chat_id": user.telegram_chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }, proxies=proxies, timeout=5)
                if res.status_code == 200:
                    logger.info(f"OTP successfully sent via Telegram bot to user {phone}")
                    return "telegram"
                else:
                    logger.warning(f"Telegram bot API returned status {res.status_code} for user {phone}: {res.text}")
            except Exception as e:
                logger.exception(f"Failed to send OTP via Telegram bot to user {phone}")

    # ۳. تلاش برای ارسال از طریق وب‌سرویس پیامک کاوه‌نگار
    if kavenegar_configured():
        if not settings.DEBUG:
            try:
                send_otp_sms(phone, otp)
                logger.info(f"OTP successfully sent via Kavenegar SMS to user {phone}")
                return "sms"
            except SMSDeliveryError as e:
                logger.error(f"Failed to send OTP via Kavenegar SMS for user {phone}: {e}")
                raise OTPDeliveryError("ارسال پیامک با خطا مواجه شد. لطفاً چند لحظه بعد دوباره تلاش کنید.") from e
        else:
            print(f"\n📱 [DEBUG MODE] OTP for {phone}: {otp}\n")
            return "debug"

    # ۴. اگر هیچ کانال ارتباطی تنظیم نشده باشد یا در حالت تست لوکال باشد
    if settings.DEBUG:
        print(f"\n📱 [DEBUG MODE] OTP for {phone}: {otp}\n")
        return "debug"

    raise OTPDeliveryError("سرویس ارسال کد تأیید پیکربندی نشده است.")
