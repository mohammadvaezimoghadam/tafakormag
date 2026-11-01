import logging
from django.conf import settings

try:
    from apps.accounts.services import send_otp_sms, SMSDeliveryError, kavenegar_configured
except ImportError:
    from backend.apps.accounts.services import send_otp_sms, SMSDeliveryError, kavenegar_configured

logger = logging.getLogger(__name__)

class OTPDeliveryError(Exception):
    """خطا در ارسال کد تایید از تمامی درگاه‌ها."""
    pass

def send_sms_otp(phone: str, otp: str) -> str:
    """
    ارسال کد تایید به شماره کاربر منحصراً از طریق پیامک کاوه‌نگار.
    در حالت DEBUG اگر کاوه‌نگار تنظیم نشده باشد، در کنسول چاپ می‌کند.
    برمی‌گرداند: 'sms' یا 'debug'
    """
    logger.info(f"[SMS OTP] Attempting to send OTP to {phone}")

    # در صورتی که کاوه‌نگار پیکربندی شده باشد
    if kavenegar_configured():
        if not settings.DEBUG:
            try:
                send_otp_sms(phone, otp)
                logger.info(f"OTP successfully sent via Kavenegar SMS to {phone}")
                return "sms"
            except SMSDeliveryError as e:
                logger.error(f"Failed to send OTP via Kavenegar SMS for {phone}: {e}")
                raise OTPDeliveryError("ارسال پیامک با خطا مواجه شد. لطفاً چند لحظه بعد تلاش کنید یا از بله استفاده کنید.") from e
        else:
            # در حالت توسعه همراه با کاوه‌نگار پیکربندی‌شده
            try:
                send_otp_sms(phone, otp)
                logger.info(f"[DEBUG MODE] OTP sent via Kavenegar SMS to {phone}")
                return "sms"
            except Exception:
                print(f"\n📱 [DEBUG MODE fallback] OTP for {phone}: {otp}\n")
                return "debug"
    
    # اگر کاوه‌نگار پیکربندی نشده باشد
    if settings.DEBUG:
        print(f"\n📱 [DEBUG MODE] OTP for {phone}: {otp}\n")
        return "debug"
        
    raise OTPDeliveryError("سرویس ارسال پیامک کاوه‌نگار پیکربندی نشده است. لطفاً از ربات بله استفاده کنید.")
