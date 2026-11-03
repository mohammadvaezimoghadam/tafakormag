import logging
from django.core.cache import cache
from django.utils import timezone
from .models import UserSubscription

logger = logging.getLogger(__name__)

# مدت زمان نگهداری کش اعتبار دسترسی (بر حسب ثانیه) - ۱۵ دقیقه
SUBSCRIPTION_CACHE_TTL = 900


def get_subscription_cache_key(user_id: int, plugin_identifier: str) -> str:
    """تولید کلید یکتای کش حافظه‌ای برای وضعیت اشتراک کاربر"""
    return f"sub_active:{user_id}:{plugin_identifier}"


def has_active_subscription(user, plugin_identifier: str) -> bool:
    """
    بررسی فوق‌العاده سریع وضعیت اشتراک فعال کاربر با پترن Cache-Aside.
    درخواست‌ها در زیر ۱ میلی‌ثانیه از رم پاسخ داده می‌شوند.
    """
    if not user or not user.is_authenticated:
        return False

    # مدیران و کارمندان سیستم به تمام افزونه‌ها دسترسی کامل دارند
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True

    cache_key = get_subscription_cache_key(user.id, plugin_identifier)
    cached_status = cache.get(cache_key)
    if cached_status is not None:
        return bool(cached_status)

    now = timezone.now()

    # کوئری تک‌مرحله‌ای با استفاده از کامپوزیت ایندکس دیتابیس (Covering Index Scan)
    is_active = UserSubscription.objects.filter(
        user_id=user.id,
        plugin_identifier__in=[plugin_identifier, 'all'],
        status='active',
        expires_at__gt=now
    ).exists()

    cache.set(cache_key, is_active, timeout=SUBSCRIPTION_CACHE_TTL)
    return is_active


def invalidate_user_subscription_cache(user_id: int, plugin_identifier: str = None) -> None:
    """
    باطل‌سازی فوری کش وضعیت کاربر پس از خرید، تمدید یا تغییر دسترسی
    """
    try:
        if plugin_identifier:
            cache.delete(get_subscription_cache_key(user_id, plugin_identifier))
            cache.delete(get_subscription_cache_key(user_id, 'all'))
        else:
            # در صورتی که پلاگین مشخص نبود، برای افزونه‌های اصلی کش پاک می‌شود
            for pid in ['quran', 'golshan_raz', 'all']:
                cache.delete(get_subscription_cache_key(user_id, pid))
    except Exception as e:
        logger.warning(f"Error invalidating subscription cache for user={user_id}: {e}")


def get_user_active_subscription(user, plugin_identifier: str):
    """
    دریافت شیء آخرین اشتراک فعال کاربر جهت نمایش تاریخ انقضا و مشخصات پلن
    """
    if not user or not user.is_authenticated:
        return None

    now = timezone.now()
    return UserSubscription.objects.filter(
        user_id=user.id,
        plugin_identifier__in=[plugin_identifier, 'all'],
        status='active',
        expires_at__gt=now
    ).select_related('plan').order_by('-expires_at').first()

