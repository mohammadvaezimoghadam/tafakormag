"""
Domain-specific exceptions for the Marketplace plugin.
These exceptions represent business rule violations (e.g. stock, coupons, permissions)
and are caught by API Views to return clean, standardized error responses.
"""


class MarketplaceError(Exception):
    """Base exception for all marketplace business logic errors."""
    default_message = "خطایی در عملیات بازارچه رخ داده است."

    def __init__(self, message=None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class ItemNotAvailableError(MarketplaceError):
    """Raised when an item is not in available status or is soft-deleted."""
    default_message = "این کالا در حال حاضر در دسترس یا فعال نیست."


class InsufficientStockError(MarketplaceError):
    """Raised when requested quantity exceeds available warehouse stock."""
    default_message = "موجودی این کالا در انبار کافی نیست."


class SelfPurchaseError(MarketplaceError):
    """Raised when a seller attempts to add their own item to their cart."""
    default_message = "شما نمی‌توانید کالای خودتان را خریداری کنید."


class DigitalItemQuantityError(MarketplaceError):
    """Raised when attempting to add more than 1 quantity for a digital download."""
    default_message = "برای فایل‌های دانلودی فقط امکان ثبت ۱ نسخه وجود دارد."


class InvalidCouponError(MarketplaceError):
    """Raised when a discount coupon is expired, inactive, or not applicable."""
    default_message = "کد تخفیف وارد شده معتبر یا قابل استفاده نیست."


class CartEmptyError(MarketplaceError):
    """Raised when attempting to checkout with an empty cart."""
    default_message = "سبد خرید شما خالی است."


class ShippingAddressRequiredError(MarketplaceError):
    """Raised when physical products are ordered without providing a shipping address."""
    default_message = "برای کالاهای فیزیکی، انتخاب آدرس تحویل گیرنده الزامی است."


class InvalidAddressError(MarketplaceError):
    """Raised when the selected shipping address does not belong to the user or is invalid."""
    default_message = "آدرس پستی انتخاب‌شده نامعتبر است."


class OrderCheckoutError(MarketplaceError):
    """Raised when an error occurs during order finalization or checkout."""
    default_message = "خطایی در نهایی‌سازی سفارش رخ داده است."


class PaymentError(MarketplaceError):
    """Raised when an error occurs during gateway communication."""
    default_message = "خطایی در اتصال یا ارتباط با درگاه بانکی رخ داده است."


class PaymentAlreadyCompletedError(MarketplaceError):
    """Raised when an order has already been paid for."""
    default_message = "این سفارش قبلاً پرداخت شده و نیازی به پرداخت مجدد ندارد."


class PaymentVerificationFailedError(MarketplaceError):
    """Raised when bank verification fails or transaction was rejected/cancelled."""
    default_message = "تراکنش بانکی تایید نشد یا توسط خریدار لغو گردید."


class DonationError(MarketplaceError):
    """Base exception for charity/donation workflow errors."""
    default_message = "خطایی در عملیات اهدای کتاب رخ داده است."


class ItemNotDonationError(DonationError):
    """Raised when attempting a donation action on a sale item."""
    default_message = "این کالا برای اهدای رایگان ثبت نشده و یک کالای فروشی است."


class SelfDonationRequestError(DonationError):
    """Raised when a donor requests their own donated item."""
    default_message = "شما نمی‌توانید برای کتاب اهدایی خودتان درخواست ثبت کنید."


class DonationAlreadyRequestedError(DonationError):
    """Raised when a user attempts duplicate requests for the same item."""
    default_message = "شما قبلاً برای این کتاب اهدایی درخواست ثبت کرده‌اید."


class UnauthorizedDonationActionError(DonationError):
    """Raised when an unauthorized user attempts to accept/reject a donation request."""
    default_message = "شما دسترسی لازم برای تصمیم‌گیری روی این درخواست اهدایی را ندارید."



