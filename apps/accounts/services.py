import logging

from django.conf import settings


logger = logging.getLogger(__name__)


class SMSDeliveryError(Exception):
    """خطا در ارسال پیامک از طریق کاوه‌نگار."""


def kavenegar_configured() -> bool:
    key = (getattr(settings, "KAVENEGAR_API_KEY", None) or "").strip()
    sender = (getattr(settings, "KAVENEGAR_SENDER", None) or "").strip()
    return bool(key and sender)


def send_otp_sms(phone: str, otp: str) -> None:
    """
    ارسال کد تأیید با وب‌سرویس کاوه‌نگار.
    نیاز به KAVENEGAR_API_KEY و KAVENEGAR_SENDER در settings دارد.
    """
    if not kavenegar_configured():
        raise SMSDeliveryError("Kavenegar API key or sender is not configured.")

    from kavenegar import APIException, HTTPException, KavenegarAPI

    api = KavenegarAPI(settings.KAVENEGAR_API_KEY.strip())
    params = {
        "sender": settings.KAVENEGAR_SENDER.strip(),
        "receptor": phone,
        "message": f"کد تأیید شما: {otp}",
    }
    try:
        api.sms_send(params)
    except (APIException, HTTPException) as e:
        logger.exception("Kavenegar sms_send failed for receptor=%s", phone)
        raise SMSDeliveryError(str(e)) from e
