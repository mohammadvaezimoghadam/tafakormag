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


class CirculationError(MarketplaceError):
    """Base exception for in-person book circulation and kiosk errors."""
    default_message = "خطایی در فرآیند گردش و اهدای کتاب رخ داده است."


class BookCopyNotFoundError(CirculationError):
    """Raised when a physical book copy cannot be resolved by its short code."""
    default_message = "نسخه فیزیکی این کتاب با شناسه وارد شده یافت نشد."


class UnauthorizedBookActionError(CirculationError):
    """Raised when a user attempts to transfer/manage a book they do not currently hold."""
    default_message = "شما در حال حاضر نگه‌دارنده این کتاب نیستید و اجازه مدیریت یا انتقال آن را ندارید."


class BookNotAvailableForHandoverError(CirculationError):
    """Raised when a book is in a state that does not allow in-person transfer (e.g. lost, retired, or in station)."""
    default_message = "این کتاب در وضعیت مجاز برای انتقال حضوری قرار ندارد."


class SelfHandoverError(CirculationError):
    """Raised when a user attempts to transfer a book to themselves."""
    default_message = "شما نمی‌توانید کتاب را به خودتان انتقال دهید."


class TransferCooldownActiveError(CirculationError):
    """Raised when attempting to transfer a book back to previous holder before the cooldown expires (ADR-009)."""
    default_message = "امکان بازگرداندن این کتاب به دارنده قبلی تا ۷۲ ساعت وجود ندارد (قانون ضدتقلب)."


class DailyTransferLimitExceededError(CirculationError):
    """Raised when a user exceeds the daily in-person donation cap (ADR-009)."""
    default_message = "شما به سقف مجاز انتقال روزانه (۲ اهدا در روز) رسیده‌اید."


class InvalidOtpError(CirculationError):
    """Raised when an OTP code for handover is incorrect or expired."""
    default_message = "کد تایید موقت وارد شده نادرست است یا مهلت زمانی آن منقضی شده است."


class StationFullError(CirculationError):
    """Raised when attempting to deposit a book into a station that is already at full capacity."""
    default_message = "ظرفیت این قفسه تفاخر تکمیل است و امکان قرار دادن کتاب جدید وجود ندارد."


class BookNotInStationError(CirculationError):
    """Raised when attempting to pickup a book that is not currently inside a station."""
    default_message = "این کتاب در حال حاضر در قفسه تفاخر قرار ندارد."


class ShelfBookError(MarketplaceError):
    """Base exception for personal bookshelf operations."""
    default_message = "خطایی در مدیریت قفسه شخصی کتاب رخ داده است."


class ShelfBookNotFoundError(ShelfBookError):
    """Raised when a shelf book record cannot be accessed or found."""
    default_message = "کتاب مورد نظر در قفسه یافت نشد."


class InvalidShelfTransitionError(ShelfBookError):
    """Raised when converting or withdrawing a shelf book violates lifecycle state rules."""
    default_message = "تغییر وضعیت درخواستی برای این کتاب مجاز نیست."





