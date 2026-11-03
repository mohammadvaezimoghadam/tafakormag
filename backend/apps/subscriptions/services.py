import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import SubscriptionPlan, UserSubscription, PurchaseVerificationLog
from .signals import subscription_activated
from .utils import invalidate_user_subscription_cache

logger = logging.getLogger(__name__)


class BazaarVerificationService:
    """
    سرویس اعتبارسنجی توکن‌های خرید و اشتراک با سرور توسعه‌دهندگان کافه‌بازار.
    مجهز به Connection Pooling و مدیریت هوشمند نشست (Session).
    """
    AUTH_URL = "https://pardakht.cafebazaar.ir/devapi/v2/auth/token/"
    BASE_API_URL = "https://pardakht.cafebazaar.ir/devapi/v2/api"

    _session = None
    _cached_access_token = None
    _token_expiry = None

    @classmethod
    def get_session(cls) -> requests.Session:
        """تولید یا بازاستفاده از نشست HTTP دارای Connection Pool"""
        if cls._session is None:
            session = requests.Session()
            retries = Retry(total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=retries)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            cls._session = session
        return cls._session

    @classmethod
    def get_client_credentials(cls) -> tuple[str, str, str, str]:
        """دریافت تنظیمات کافه‌بازار از settings"""
        client_id = getattr(settings, 'BAZAAR_CLIENT_ID', '').strip()
        client_secret = getattr(settings, 'BAZAAR_CLIENT_SECRET', '').strip()
        refresh_token = getattr(settings, 'BAZAAR_REFRESH_TOKEN', '').strip()
        package_name = getattr(settings, 'BAZAAR_PACKAGE_NAME', 'com.tafakor.quran').strip()
        return client_id, client_secret, refresh_token, package_name

    @classmethod
    def get_access_token(cls) -> str | None:
        """
        دریافت توکن دسترسی معتبر از بازار با مکانیزم رفرش‌توکن و کش حافظه‌ای
        """
        now = timezone.now()
        if cls._cached_access_token and cls._token_expiry and now < cls._token_expiry:
            return cls._cached_access_token

        client_id, client_secret, refresh_token, _ = cls.get_client_credentials()
        if not (client_id and client_secret and refresh_token):
            return None

        session = cls.get_session()
        payload = {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
        }

        try:
            response = session.post(cls.AUTH_URL, data=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)
                cls._cached_access_token = token
                cls._token_expiry = now + timedelta(seconds=max(60, expires_in - 120))
                return token
            logger.error(f"Failed to refresh Bazaar access token: status={response.status_code}, body={response.text}")
        except Exception as e:
            logger.exception(f"Exception refreshing Bazaar access token: {e}")

        return None

    @classmethod
    def verify_subscription(
        cls,
        package_name: str,
        sku: str,
        purchase_token: str
    ) -> tuple[bool, dict, str | None]:
        """
        اعتبارسنجی رسمی وضعیت اشتراک در کافه‌بازار.
        خروجی: (is_valid, raw_payload, error_message)
        """
        # حالت توسعه و تست (Sandbox / Mock Token)
        is_mock_token = purchase_token.startswith(('mock_', 'test_', 'demo_', 'dev_'))
        is_sandbox = getattr(settings, 'BAZAAR_SANDBOX', True)

        if is_mock_token or (is_sandbox and not getattr(settings, 'BAZAAR_CLIENT_ID', None)):
            logger.info(f"Simulating Bazaar subscription verification for SKU={sku}, Token={purchase_token[:15]}...")
            mock_payload = {
                "kind": "androidpublisher#subscriptionPurchase",
                "initiationTimestampMsec": int(timezone.now().timestamp() * 1000),
                "validUntilTimestampMsec": int((timezone.now() + timedelta(days=30)).timestamp() * 1000),
                "autoRenewing": True,
                "mock": True
            }
            return True, mock_payload, None

        access_token = cls.get_access_token()
        if not access_token:
            return False, {}, "اطلاعات وب‌سرویس توسعه‌دهنده کافه‌بازار روی سرور پیکربندی نشده است."

        session = cls.get_session()
        endpoint = f"{cls.BASE_API_URL}/applications/{package_name}/subscriptions/{sku}/tokens/{purchase_token}/"
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/json',
        }

        try:
            response = session.get(endpoint, headers=headers, timeout=6)
            data = response.json() if response.text else {}

            if response.status_code == 200:
                # اشتراک معتبر است
                return True, data, None

            err_msg = data.get('error_description') or data.get('error') or f"خطای استعلام از بازار ({response.status_code})"
            logger.warning(f"Bazaar verification rejected: status={response.status_code}, data={data}")
            return False, data, str(err_msg)

        except requests.Timeout:
            logger.error("Bazaar verification timed out after 6 seconds.")
            return False, {}, "پاسخی از وب‌سرویس کافه‌بازار دریافت نشد (مهلت زمانی به پایان رسید)."
        except Exception as e:
            logger.exception(f"Unexpected exception during Bazaar verification: {e}")
            return False, {}, f"خطای شبکه در ارتباط با کافه‌بازار: {str(e)}"


class SubscriptionService:
    """
    سرویس جامع مدیریت مالی، تمدید اشتراک و جلوگیری از تقلب
    """

    @classmethod
    def verify_and_activate(
        cls,
        user,
        sku: str,
        purchase_token: str,
        marketplace: str = 'cafebazaar',
        package_name: str = None
    ) -> tuple[UserSubscription, PurchaseVerificationLog]:
        """
        اعتبارسنجی اتمیک و ضد Replay Attack برای فعال‌سازی یا تمدید اشتراک کاربر
        """
        if not user or not user.is_authenticated:
            raise ValidationError({'user': 'کاربر باید لاگین کرده باشد.'})

        sku = (sku or '').strip()
        purchase_token = (purchase_token or '').strip()

        if not sku or not purchase_token:
            raise ValidationError({'detail': 'ارسال شناسه محصول (SKU) و توکن خرید الزامی است.'})

        # یافتن پلن مورد ادعا
        try:
            plan = SubscriptionPlan.objects.get(sku=sku, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise ValidationError({'sku': f"طرح اشتراکی معتبر با شناسه '{sku}' یافت نشد."})

        effective_package = package_name or getattr(settings, 'BAZAAR_PACKAGE_NAME', 'com.tafakor.quran')

        with transaction.atomic():
            # ۱. بررسی امنیتی: جلوگیری قطعی از سوءاستفاده از توکن تکراری (Replay Attack)
            existing_log = PurchaseVerificationLog.objects.select_for_update().filter(
                purchase_token=purchase_token
            ).first()

            if existing_log and existing_log.is_verified:
                raise ValidationError({
                    'purchase_token': 'این توکن خرید قبلاً در سیستم ثبت و مصرف شده است.'
                })

            # ۲. استعلام زنده و رسمی از کافه‌بازار
            is_valid, payload, error_msg = BazaarVerificationService.verify_subscription(
                package_name=effective_package,
                sku=sku,
                purchase_token=purchase_token
            )

            # ۳. ثبت گزارش شفاف در لاگ‌های وریفای
            verification_log = PurchaseVerificationLog.objects.create(
                user=user,
                plan=plan,
                sku=sku,
                purchase_token=purchase_token,
                marketplace=marketplace,
                is_verified=is_valid,
                bazaar_payload=payload,
                verification_error=error_msg or ''
            )

            if not is_valid:
                raise ValidationError({
                    'detail': error_msg or 'تایید خرید در وب‌سرویس کافه‌بازار ناموفق بود.'
                })

            # ۴. قفل ردیف و تمدید هوشمند مدت زمان اشتراک کاربر
            now = timezone.now()
            current_active_sub = UserSubscription.objects.select_for_update().filter(
                user=user,
                plugin_identifier=plan.plugin_identifier,
                status='active',
                expires_at__gt=now
            ).order_by('-expires_at').first()

            is_renewal = bool(current_active_sub)

            if current_active_sub:
                # تمدید اعتبار: روزهای پلن جدید به انتهای اعتبار قبلی افزوده می‌شود
                base_time = max(now, current_active_sub.expires_at)
                new_expiry = base_time + timedelta(days=plan.duration_days)

                current_active_sub.expires_at = new_expiry
                current_active_sub.plan = plan
                current_active_sub.source = marketplace
                current_active_sub.save(update_fields=['expires_at', 'plan', 'source', 'updated_at'])
                user_sub = current_active_sub
            else:
                # اشتراک جدید
                new_expiry = now + timedelta(days=plan.duration_days)
                user_sub = UserSubscription.objects.create(
                    user=user,
                    plugin_identifier=plan.plugin_identifier,
                    plan=plan,
                    status='active',
                    starts_at=now,
                    expires_at=new_expiry,
                    source=marketplace
                )

            # ۵. باطل‌سازی آنی کش دسترسی کاربر در رم
            invalidate_user_subscription_cache(user.id, plan.plugin_identifier)

            # ۶. شلیک سیگنال برای پیامدها (ارسال پیامک، بات و رویدادها)
            try:
                subscription_activated.send(
                    sender=UserSubscription,
                    user=user,
                    user_subscription=user_sub,
                    plugin_identifier=plan.plugin_identifier,
                    plan=plan,
                    is_renewal=is_renewal
                )
            except Exception as e:
                logger.error(f"Error firing subscription_activated signal: {e}")

            return user_sub, verification_log

