from rest_framework import status
from rest_framework.exceptions import APIException


class PaymentDomainError(APIException):
    """Base exception for centralized payment gateway and settlement errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "خطایی در عملیات پرداخت رخ داده است."
    default_code = "PAYMENT_ERROR"

    def __init__(self, message: str | None = None, code: str | None = None):
        resolved_message = message or str(self.default_detail)
        super().__init__(detail=resolved_message, code=code or self.default_code)
        self.message = resolved_message


class GatewayRequestError(PaymentDomainError):
    """Raised when initiating a payment session with an external gateway fails."""

    default_detail = "خطا در برقراری ارتباط با درگاه پرداخت."
    default_code = "GATEWAY_REQUEST_ERROR"


class GatewayVerificationError(PaymentDomainError):
    """Raised when gateway callback verification fails or transaction was canceled."""

    default_detail = "تایید تراکنش در درگاه بانکی ناموفق بود یا توسط کاربر لغو شد."
    default_code = "GATEWAY_VERIFICATION_ERROR"


class PaymentNotFoundError(PaymentDomainError):
    """Raised when no payment transaction matches the provided reference or authority."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "تراکنش پرداخت مورد نظر یافت نشد."
    default_code = "PAYMENT_NOT_FOUND"


class PaymentHandlerMissingError(PaymentDomainError):
    """Raised when no domain fulfillment handler is registered for a payment purpose."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "پردازشگر تکمیل سفارش برای این نوع پرداخت ثبت نشده است."
    default_code = "PAYMENT_HANDLER_MISSING"

