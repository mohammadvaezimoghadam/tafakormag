import uuid
import logging
import requests
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import DonationTransaction, DonationCampaign

logger = logging.getLogger(__name__)


class ZarinPalService:
    @classmethod
    def get_base_url(cls) -> str:
        if getattr(settings, 'ZARINPAL_SANDBOX', True):
            return 'https://sandbox.zarinpal.com/pg'
        return 'https://payment.zarinpal.com/pg'

    @classmethod
    def get_merchant_id(cls) -> str:
        return getattr(settings, 'ZARINPAL_MERCHANT_ID', '00000000-0000-0000-0000-000000000000')

    @classmethod
    def request_payment(
        cls,
        amount_tomans: int,
        description: str,
        callback_url: str,
        mobile: str = None,
        email: str = None
    ) -> tuple[bool, str | None, str | None, str | None]:
        """
        Sends a payment request to ZarinPal (Sandbox or Production).
        Returns: (success, authority, gateway_startpay_url, error_message)
        """
        merchant_id = cls.get_merchant_id()
        base_url = cls.get_base_url()
        endpoint = f"{base_url}/v4/payment/request.json"

        payload = {
            "merchant_id": merchant_id,
            "amount": int(amount_tomans),
            "currency": "IRT",
            "description": description or "حمایت از پویش مهربانی",
            "callback_url": callback_url,
            "metadata": {}
        }
        if mobile:
            payload["metadata"]["mobile"] = str(mobile)
        if email:
            payload["metadata"]["email"] = str(email)

        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            res_data = response.json()
            
            data = res_data.get("data")
            errors = res_data.get("errors")
            
            if isinstance(data, dict) and data.get("code") == 100:
                authority = data.get("authority")
                startpay_url = f"{base_url}/StartPay/{authority}"
                return True, authority, startpay_url, None
            
            err_msg = "خطا در برقراری ارتباط با درگاه زرین‌پال"
            if errors:
                if isinstance(errors, dict) and "message" in errors:
                    err_msg = errors.get("message")
                elif isinstance(errors, list) and len(errors) > 0:
                    err_msg = str(errors[0])
                elif isinstance(errors, str):
                    err_msg = errors
            elif data and data.get("message"):
                err_msg = data.get("message")
            
            logger.error(f"ZarinPal request failed: {res_data}")
            return False, None, None, err_msg
        except Exception as e:
            logger.exception(f"Exception requesting payment from ZarinPal: {e}")
            return False, None, None, f"خطای ارتباط با درگاه پرداخت: {str(e)}"

    @classmethod
    def verify_payment(
        cls,
        authority: str,
        amount_tomans: int
    ) -> tuple[bool, int | None, str | None, int | None, str | None]:
        """
        Verifies a payment with ZarinPal.
        Returns: (success, ref_id, card_pan, fee, error_message)
        """
        merchant_id = cls.get_merchant_id()
        base_url = cls.get_base_url()
        endpoint = f"{base_url}/v4/payment/verify.json"

        payload = {
            "merchant_id": merchant_id,
            "amount": int(amount_tomans),
            "authority": authority
        }

        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            res_data = response.json()

            data = res_data.get("data")
            errors = res_data.get("errors")

            # Code 100: First-time success, Code 101: Already Verified
            if isinstance(data, dict) and data.get("code") in [100, 101]:
                ref_id = data.get("ref_id")
                card_pan = data.get("card_pan")
                fee = data.get("fee")
                return True, ref_id, card_pan, fee, None

            err_msg = "تایید پرداخت در زرین‌پال ناموفق بود."
            if errors:
                if isinstance(errors, dict) and "message" in errors:
                    err_msg = errors.get("message")
                elif isinstance(errors, list) and len(errors) > 0:
                    err_msg = str(errors[0])
                elif isinstance(errors, str):
                    err_msg = errors
            elif data and data.get("message"):
                err_msg = data.get("message")

            logger.warning(f"ZarinPal verify failed: {res_data}")
            return False, None, None, None, err_msg
        except Exception as e:
            logger.exception(f"Exception verifying payment with ZarinPal: {e}")
            return False, None, None, None, f"خطای شبکه در تایید پرداخت: {str(e)}"


def initiate_donation(
    campaign_id,
    amount: int,
    is_anonymous: bool = False,
    donor=None,
    callback_url: str = None
) -> tuple[DonationTransaction, str]:
    """
    Initiates a new donation transaction in PENDING status, connects to ZarinPal
    gateway to obtain a valid authority and startpay redirect URL.
    """
    try:
        campaign = DonationCampaign.objects.get(id=campaign_id)
    except DonationCampaign.DoesNotExist:
        raise ValidationError({'campaign': 'پویش مورد نظر یافت نشد.'})

    if campaign.status != DonationCampaign.StatusChoices.ACTIVE:
        raise ValidationError({'campaign': 'امکان پرداخت برای این پویش وجود ندارد (پویش فعال نیست).'})

    if campaign.deadline and timezone.now() > campaign.deadline:
        campaign.check_and_update_status()
        raise ValidationError({'campaign': 'مهلت زمانی این پویش به پایان رسیده است.'})

    if amount < 1000:
        raise ValidationError({'amount': 'حداقل مبلغ واریزی ۱,۰۰۰ تومان است.'})

    backend_base = getattr(settings, 'BACKEND_BASE_URL', 'http://localhost:8000').rstrip('/')
    effective_callback = callback_url or f"{backend_base}/api/v1/donations/payment/callback/"

    mobile = donor.phone if donor and hasattr(donor, 'phone') and not is_anonymous else None
    description = f"حمایت از پویش {campaign.title[:50]}"

    success, authority, gateway_url, error_msg = ZarinPalService.request_payment(
        amount_tomans=amount,
        description=description,
        callback_url=effective_callback,
        mobile=mobile
    )

    if not success or not authority or not gateway_url:
        raise ValidationError({'gateway': error_msg or 'خطا در ارتباط با درگاه پرداخت زرین‌پال.'})

    trx = DonationTransaction.objects.create(
        campaign=campaign,
        donor=donor if donor and donor.is_authenticated else None,
        amount=amount,
        is_anonymous=is_anonymous,
        status=DonationTransaction.PaymentStatus.PENDING,
        authority=authority
    )

    return trx, gateway_url



def verify_and_settle_transaction(
    authority: str,
    gateway_ref: str = None,
    tracking_code: str = None
) -> DonationTransaction:
    """
    Idempotent and Atomic financial transaction settlement.
    Safeguards against race conditions using row-level locking (select_for_update)
    and atomic F() increments.
    """
    with transaction.atomic():
        # 1. Lock transaction row
        try:
            trx = DonationTransaction.objects.select_for_update().get(authority=authority)
        except DonationTransaction.DoesNotExist:
            raise ValidationError({'authority': 'تراکنش با این شناسه یافت نشد.'})

        if trx.status == DonationTransaction.PaymentStatus.SUCCESSFUL:
            return trx  # Already settled (Idempotency safeguard)

        # 2. Lock associated campaign row
        campaign = DonationCampaign.objects.select_for_update().get(id=trx.campaign_id)
        
        # 3. Mark transaction as successful
        trx.status = DonationTransaction.PaymentStatus.SUCCESSFUL
        trx.gateway_reference_id = gateway_ref or f"REF_{uuid.uuid4().hex[:12].upper()}"
        trx.tracking_code = tracking_code or f"TRK_{uuid.uuid4().hex[:8].upper()}"
        trx.completed_at = timezone.now()
        trx.save(update_fields=['status', 'gateway_reference_id', 'tracking_code', 'completed_at'])

        # 4. Atomic increment on campaign metrics (handles overfunding naturally)
        DonationCampaign.objects.filter(id=campaign.id).update(
            collected_amount=F('collected_amount') + trx.amount,
            donors_count=F('donors_count') + 1,
            updated_at=timezone.now()
        )

        # 5. Reload and check completion threshold
        campaign.refresh_from_db()
        campaign.check_and_update_status()

        return trx
