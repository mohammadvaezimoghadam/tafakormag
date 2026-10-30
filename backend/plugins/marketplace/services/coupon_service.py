from decimal import Decimal
from typing import Dict, Any, List
from django.utils import timezone
from django.db import models

from ..models.discount import Coupon, CouponUsage
from ..exceptions import InvalidCouponError


class CouponService:
    """
    Dedicated service managing promotional vouchers, seller-specific coupons,
    usage caps, and discount calculations.
    """

    @classmethod
    def validate_and_calculate_discount(
        cls,
        code: str,
        user,
        cart_items: list,
        total_items_amount: Decimal
    ) -> Dict[str, Any]:
        """
        Validates coupon conditions against user and cart:
        - Expiration dates (valid_from, valid_until).
        - Global and per-user usage limits.
        - Minimum order value threshold.
        - Seller-scoped coupons (valid only if cart contains items from that seller).
        Returns calculated discount amount and bearer details.
        """
        if not code or not code.strip():
            raise InvalidCouponError("کد تخفیف معتبر نیست.")

        try:
            coupon = Coupon.objects.get(code__iexact=code.strip(), is_active=True)
        except Coupon.DoesNotExist:
            raise InvalidCouponError("کد تخفیف وارد شده یافت نشد یا غیرفعال است.")

        now = timezone.now()

        # 1. Date window validation
        if coupon.valid_from and now < coupon.valid_from:
            raise InvalidCouponError("زمان استفاده از این کد تخفیف هنوز فرا نرسیده است.")
        if coupon.valid_until and now > coupon.valid_until:
            raise InvalidCouponError("مهلت استفاده از این کد تخفیف به پایان رسیده است.")

        # 2. Global usage limit
        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            raise InvalidCouponError("سقف استفاده از این کد تخفیف به اتمام رسیده است.")

        # 3. Per-user usage limit
        if user and user.is_authenticated:
            user_used_count = CouponUsage.objects.filter(coupon=coupon, user=user).count()
            if user_used_count >= coupon.user_usage_limit:
                raise InvalidCouponError(
                    f"شما قبلاً از این کد تخفیف به میزان حداکثر مجاز ({coupon.user_usage_limit} بار) استفاده کرده‌اید."
                )

        # 4. Seller scope: If coupon belongs to a specific vendor, calculate discount only on vendor's items
        applicable_amount = total_items_amount
        if coupon.seller_id:
            vendor_amount = sum(
                (ci.item.discount_price if ci.item.discount_price else ci.item.price) * ci.quantity
                for ci in cart_items
                if ci.item.seller_id == coupon.seller_id
            )
            if vendor_amount <= 0:
                raise InvalidCouponError("این کد تخفیف فقط برای محصولات فروشنده خاصی تعریف شده است.")
            applicable_amount = vendor_amount

        # 5. Minimum order amount threshold
        if coupon.min_order_amount and applicable_amount < coupon.min_order_amount:
            raise InvalidCouponError(
                f"حداقل مبلغ خرید برای اعمال این کد تخفیف {coupon.min_order_amount:,.0f} تومان است."
            )

        # 6. Calculate discount value
        if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
            discount_amount = (applicable_amount * coupon.discount_value) / Decimal("100")
            if coupon.max_discount_amount and discount_amount > coupon.max_discount_amount:
                discount_amount = coupon.max_discount_amount
        else:
            discount_amount = coupon.discount_value

        # Discount cannot exceed applicable amount
        if discount_amount > applicable_amount:
            discount_amount = applicable_amount

        return {
            "coupon": coupon,
            "discount_amount": discount_amount,
            "discount_bearer": coupon.discount_bearer,
            "applicable_amount": applicable_amount,
        }

    @classmethod
    def record_usage(cls, coupon: Coupon, user, order, discount_amount: Decimal) -> CouponUsage:
        """
        Records the successful redemption of a coupon and atomically increments usage counters.
        """
        usage, _ = CouponUsage.objects.get_or_create(
            coupon=coupon,
            user=user,
            order=order,
            defaults={"discount_applied": discount_amount}
        )
        Coupon.objects.filter(id=coupon.id).update(used_count=models.F("used_count") + 1)
        return usage
