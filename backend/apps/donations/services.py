import logging
import uuid
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from apps.payments.exceptions import PaymentDomainError, PaymentNotFoundError
from apps.payments.gateways.zarinpal import ZarinPalGateway
from apps.payments.models import PaymentTransaction
from apps.payments.services import CallbackOutcome, PaymentService
from .models import DonationCampaign, DonationTransaction, PayoutRequest

logger = logging.getLogger(__name__)


class ZarinPalService:
    """
    Compatibility facade delegating all ZarinPal HTTP operations to apps.payments.ZarinPalGateway.
    """

    @classmethod
    def get_base_url(cls) -> str:
        return ZarinPalGateway.get_base_url()

    @classmethod
    def get_merchant_id(cls) -> str:
        return ZarinPalGateway.get_merchant_id()

    @classmethod
    def request_payment(
        cls,
        amount_tomans: int,
        description: str,
        callback_url: str,
        mobile: str = None,
        email: str = None,
    ) -> tuple[bool, str | None, str | None, str | None]:
        """Delegate payment request initiation to centralized ZarinPalGateway."""
        res = ZarinPalGateway().request_payment(
            amount_tomans=amount_tomans,
            description=description,
            callback_url=callback_url,
            mobile=mobile,
            email=email,
        )
        return res.success, res.authority, res.gateway_url, res.error_message

    @classmethod
    def verify_payment(
        cls,
        authority: str,
        amount_tomans: int,
    ) -> tuple[bool, int | str | None, str | None, int | None, str | None]:
        """Delegate transaction verification to centralized ZarinPalGateway."""
        res = ZarinPalGateway().verify_payment(
            authority=authority,
            amount_tomans=amount_tomans,
        )
        parsed_ref: int | str | None = res.ref_id
        if isinstance(res.ref_id, str) and res.ref_id.isdigit():
            parsed_ref = int(res.ref_id)
        return res.success, parsed_ref, res.card_pan or None, res.fee, res.error_message


def initiate_donation(
    campaign_id,
    amount: int,
    is_anonymous: bool = False,
    donor=None,
    callback_url: str = None,
) -> tuple[DonationTransaction, str]:
    """
    Validate campaign state and initiate a donation payment through centralized PaymentService.
    """
    try:
        campaign = DonationCampaign.objects.get(id=campaign_id)
    except DonationCampaign.DoesNotExist:
        raise ValidationError({"campaign": "پویش مورد نظر یافت نشد."})

    if campaign.status != DonationCampaign.StatusChoices.ACTIVE:
        raise ValidationError({"campaign": "امکان پرداخت برای این پویش وجود ندارد (پویش فعال نیست)."})

    if campaign.deadline and timezone.now() > campaign.deadline:
        campaign.check_and_update_status()
        raise ValidationError({"campaign": "مهلت زمانی این پویش به پایان رسیده است."})

    if amount < 1000:
        raise ValidationError({"amount": "حداقل مبلغ واریزی ۱,۰۰۰ تومان است."})

    mobile = donor.phone if donor and hasattr(donor, "phone") and not is_anonymous else None
    description = f"حمایت از پویش {campaign.title[:50]}"

    try:
        central_trx, gateway_url = PaymentService.initiate_payment(
            purpose=PaymentTransaction.Purpose.DONATION,
            reference_id=str(campaign.id),
            amount_tomans=amount,
            user=donor,
            description=description,
            callback_url=callback_url or "",
            gateway_name=PaymentTransaction.Gateway.ZARINPAL,
            mobile=mobile,
            metadata={
                "campaign_id": str(campaign.id),
                "is_anonymous": bool(is_anonymous),
            },
        )
    except PaymentDomainError as exc:
        raise ValidationError({"gateway": exc.message}) from exc

    trx = DonationTransaction.objects.create(
        campaign=campaign,
        donor=donor if donor and getattr(donor, "is_authenticated", False) else None,
        payment_transaction=central_trx,
        amount=amount,
        is_anonymous=is_anonymous,
        status=DonationTransaction.PaymentStatus.PENDING,
        authority=central_trx.authority,
    )
    return trx, gateway_url or ""


def verify_and_settle_transaction(
    authority: str,
    gateway_ref: str = None,
    tracking_code: str = None,
) -> DonationTransaction:
    """
    Idempotent and atomic financial settlement for DonationTransaction and DonationCampaign.
    """
    with transaction.atomic():
        try:
            trx = DonationTransaction.objects.select_for_update().get(authority=authority)
        except DonationTransaction.DoesNotExist:
            raise ValidationError({"authority": "تراکنش با این شناسه یافت نشد."})

        if trx.status == DonationTransaction.PaymentStatus.SUCCESSFUL:
            return trx

        campaign = DonationCampaign.objects.select_for_update().get(id=trx.campaign_id)

        trx.status = DonationTransaction.PaymentStatus.SUCCESSFUL
        trx.gateway_reference_id = gateway_ref or f"REF_{uuid.uuid4().hex[:12].upper()}"
        trx.tracking_code = tracking_code or f"TRK_{uuid.uuid4().hex[:8].upper()}"
        trx.completed_at = timezone.now()
        trx.save(update_fields=["status", "gateway_reference_id", "tracking_code", "completed_at"])

        if trx.payment_transaction_id:
            PaymentTransaction.objects.filter(pk=trx.payment_transaction_id).exclude(
                status=PaymentTransaction.Status.SUCCESSFUL
            ).update(
                status=PaymentTransaction.Status.SUCCESSFUL,
                ref_id=trx.gateway_reference_id,
                tracking_code=trx.tracking_code,
                settled_at=trx.completed_at,
                updated_at=timezone.now(),
            )

        DonationCampaign.objects.filter(id=campaign.id).update(
            collected_amount=F("collected_amount") + trx.amount,
            donors_count=F("donors_count") + 1,
            updated_at=timezone.now(),
        )

        campaign.refresh_from_db()
        campaign.check_and_update_status()
        return trx


def handle_donation_callback(
    *,
    authority: str | None,
    status_param: str,
    frontend_base: str,
) -> CallbackOutcome:
    """
    Process browser callback for donations via central PaymentService, falling back
    cleanly for legacy DonationTransaction rows created without a PaymentTransaction.
    """
    if authority and PaymentTransaction.objects.filter(authority=authority).exists():
        return PaymentService.process_gateway_callback(
            authority=authority,
            status_param=status_param,
            host_base=frontend_base,
        )

    if not authority:
        return CallbackOutcome(
            success=False,
            status_label="failed",
            reason="missing_authority",
            payment_trx=None,
            redirect_url=f"{frontend_base}/donate?payment=failed&reason=missing_authority",
        )

    try:
        trx = DonationTransaction.objects.get(authority=authority)
    except DonationTransaction.DoesNotExist:
        return CallbackOutcome(
            success=False,
            status_label="failed",
            reason="not_found",
            payment_trx=None,
            redirect_url=f"{frontend_base}/donate?payment=failed&authority={authority}&reason=not_found",
        )

    if (status_param or "").upper() != "OK":
        if trx.status == DonationTransaction.PaymentStatus.PENDING:
            trx.status = DonationTransaction.PaymentStatus.FAILED
            trx.save(update_fields=["status"])
        return CallbackOutcome(
            success=False,
            status_label="failed",
            reason="canceled",
            payment_trx=None,
            redirect_url=f"{frontend_base}/donate?payment=failed&authority={authority}&reason=canceled&campaign_id={trx.campaign_id}",
        )

    if trx.status == DonationTransaction.PaymentStatus.SUCCESSFUL:
        ref_id = trx.gateway_reference_id or trx.tracking_code or authority
        return CallbackOutcome(
            success=True,
            status_label="success",
            reason="",
            payment_trx=None,
            redirect_url=f"{frontend_base}/donate?payment=success&authority={authority}&ref_id={ref_id}&amount={trx.amount}&campaign_id={trx.campaign_id}",
        )

    verify_res = ZarinPalGateway().verify_payment(authority=authority, amount_tomans=trx.amount)
    if verify_res.success:
        settled_trx = verify_and_settle_transaction(
            authority=authority,
            gateway_ref=verify_res.ref_id or None,
            tracking_code=verify_res.ref_id or None,
        )
        return CallbackOutcome(
            success=True,
            status_label="success",
            reason="",
            payment_trx=None,
            redirect_url=f"{frontend_base}/donate?payment=success&authority={authority}&ref_id={settled_trx.gateway_reference_id}&amount={settled_trx.amount}&campaign_id={settled_trx.campaign_id}",
        )

    trx.status = DonationTransaction.PaymentStatus.FAILED
    trx.save(update_fields=["status"])
    return CallbackOutcome(
        success=False,
        status_label="failed",
        reason="verification_failed",
        payment_trx=None,
        redirect_url=f"{frontend_base}/donate?payment=failed&authority={authority}&reason=verification_failed&campaign_id={trx.campaign_id}",
    )


def verify_donation_payment(
    *,
    authority: str,
    gateway_ref: str | None = None,
    tracking_code: str | None = None,
) -> DonationTransaction:
    """
    Programmatic donation verification delegating to central PaymentService when linked,
    with fallback to ZarinPalGateway for legacy unlinked DonationTransaction rows.
    """
    if PaymentTransaction.objects.filter(authority=authority).exists():
        try:
            central_trx, _ = PaymentService.verify_and_finalize(
                authority=authority,
                status_param="OK",
                gateway_ref=gateway_ref,
                tracking_code=tracking_code,
            )
        except PaymentNotFoundError as exc:
            raise NotFound("تراکنش با این شناسه یافت نشد.") from exc
        except PaymentDomainError as exc:
            raise ValidationError({"error": exc.message}) from exc
        return DonationTransaction.objects.get(authority=central_trx.authority)

    try:
        trx_obj = DonationTransaction.objects.get(authority=authority)
    except DonationTransaction.DoesNotExist as exc:
        raise NotFound("تراکنش با این شناسه یافت نشد.") from exc

    if not gateway_ref and trx_obj.status != DonationTransaction.PaymentStatus.SUCCESSFUL:
        verify_res = ZarinPalGateway().verify_payment(
            authority=authority,
            amount_tomans=trx_obj.amount,
        )
        if not verify_res.success:
            trx_obj.status = DonationTransaction.PaymentStatus.FAILED
            trx_obj.save(update_fields=["status"])
            raise ValidationError({"error": verify_res.error_message or "اعتبارسنجی درگاه ناموفق بود."})
        gateway_ref = verify_res.ref_id
        tracking_code = verify_res.ref_id

    return verify_and_settle_transaction(
        authority=authority,
        gateway_ref=gateway_ref,
        tracking_code=tracking_code,
    )


def validate_iran_iban(iban: str) -> str:
    """Validate and normalize an Iranian Sheba/IBAN string."""
    cleaned = "".join(str(iban or "").split()).upper()
    if not cleaned:
        raise ValidationError({"iban": "شماره شبا الزامی است."})

    if not cleaned.startswith("IR"):
        cleaned = f"IR{cleaned}"

    if len(cleaned) != 26 or not cleaned[2:].isdigit():
        raise ValidationError({
            "iban": "شماره شبا نامعتبر است. فرمت صحیح: IR به همراه ۲۴ رقم عددی می‌باشد."
        })
    return cleaned


def create_payout_request(
    *,
    campaign_id,
    user,
    amount: int,
    iban: str,
    account_holder_name: str,
) -> PayoutRequest:
    """
    Validate balance, IBAN, user permission and record a PayoutRequest atomically.
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied("برای درخواست تسویه حساب، ابتدا وارد سامانه شوید.")

    normalized_iban = validate_iran_iban(iban)
    holder_name = (account_holder_name or "").strip()
    if not holder_name:
        raise ValidationError({"account_holder_name": "نام و نام خانوادگی صاحب حساب الزامی است."})

    req_amount = int(amount)
    if req_amount < 10000:
        raise ValidationError({"amount": "حداقل مبلغ قابل تسویه ۱۰,۰۰۰ تومان است."})

    with transaction.atomic():
        try:
            campaign = DonationCampaign.objects.select_for_update().get(id=campaign_id)
        except DonationCampaign.DoesNotExist:
            raise NotFound("پویش مورد نظر یافت نشد.")

        is_owner = campaign.creator_id == user.id
        is_staff = user.is_staff or user.is_superuser
        if not (is_owner or is_staff):
            raise PermissionDenied("شما مجاز به ثبت درخواست تسویه برای این پویش نیستید.")

        # Ensure campaign is ended before allowing regular creator payout
        if not campaign.is_ended and not is_staff:
            raise ValidationError({
                "detail": "امکان درخواست تسویه حساب تنها پس از پایان مهلت زمانی پویش یا تکمیل ۱۰۰٪ مبلغ هدف وجود دارد."
            })

        # Check for duplicate pending requests
        has_pending = campaign.payout_requests.filter(
            status__in=[PayoutRequest.Status.PENDING, PayoutRequest.Status.APPROVED]
        ).exists()
        if has_pending:
            raise ValidationError({
                "detail": "یک درخواست تسویه در حال بررسی برای این پویش وجود دارد. لطفا تا تعیین تکلیف آن صبر فرمایید."
            })

        available_balance = campaign.available_payout_balance
        if req_amount > available_balance:
            raise ValidationError({
                "amount": f"مبلغ درخواستی ({req_amount:,} تومان) بیشتر از موجودی قابل تسویه پویش ({available_balance:,} تومان) است."
            })

        payout = PayoutRequest.objects.create(
            campaign=campaign,
            requested_by=user,
            amount=req_amount,
            iban=normalized_iban,
            account_holder_name=holder_name,
            status=PayoutRequest.Status.PENDING,
        )

        logger.info(
            "Payout request created: id=%s campaign=%s amount=%s by user=%s",
            payout.id,
            campaign.id,
            payout.amount,
            user.id,
        )
        return payout


def process_payout_settlement(
    *,
    payout_id,
    admin_user,
    action: str,
    tracking_number: str = "",
    receipt_file=None,
    rejection_reason: str = "",
    notes: str = "",
) -> PayoutRequest:
    """
    Process, complete, or reject a PayoutRequest. Staff/admin only.
    """
    if not admin_user or not (admin_user.is_staff or admin_user.is_superuser):
        raise PermissionDenied("تنها مدیران ارشد مجاز به پردازش و تسویه حساب هستند.")

    normalized_action = (action or "").strip().lower()
    if normalized_action not in ("complete", "reject", "approve"):
        raise ValidationError({"action": "عملیات نامعتبر است. گزینه‌های مجاز: complete, reject, approve"})

    with transaction.atomic():
        try:
            payout = PayoutRequest.objects.select_for_update().select_related("campaign").get(id=payout_id)
        except PayoutRequest.DoesNotExist:
            raise NotFound("درخواست تسویه مورد نظر یافت نشد.")

        if payout.status == PayoutRequest.Status.COMPLETED:
            raise ValidationError({"detail": "این درخواست قبلاً تسویه و تکمیل گردیده است."})

        if normalized_action == "complete":
            clean_track = (tracking_number or "").strip()
            if not clean_track:
                raise ValidationError({"tracking_number": "وارد کردن شماره پیگیری فیش بانکی (ساتنا/پایا) برای تکمیل تسویه الزامی است."})

            payout.status = PayoutRequest.Status.COMPLETED
            payout.tracking_number = clean_track
            payout.settled_at = timezone.now()
            payout.processed_by = admin_user
            if receipt_file:
                payout.receipt_file = receipt_file
            if notes:
                payout.admin_notes = notes

            payout.save(update_fields=[
                "status", "tracking_number", "settled_at", "processed_by", "receipt_file", "admin_notes", "updated_at"
            ])
            logger.info("Payout %s completed by admin %s (track=%s)", payout.id, admin_user.id, clean_track)

        elif normalized_action == "reject":
            clean_reason = (rejection_reason or "").strip()
            if not clean_reason:
                raise ValidationError({"rejection_reason": "ذکر علت رد درخواست الزامی است."})

            payout.status = PayoutRequest.Status.REJECTED
            payout.rejection_reason = clean_reason
            payout.processed_by = admin_user
            if notes:
                payout.admin_notes = notes

            payout.save(update_fields=[
                "status", "rejection_reason", "processed_by", "admin_notes", "updated_at"
            ])
            logger.info("Payout %s rejected by admin %s: %s", payout.id, admin_user.id, clean_reason)

        elif normalized_action == "approve":
            payout.status = PayoutRequest.Status.APPROVED
            payout.processed_by = admin_user
            if notes:
                payout.admin_notes = notes
            payout.save(update_fields=["status", "processed_by", "admin_notes", "updated_at"])
            logger.info("Payout %s marked approved by admin %s", payout.id, admin_user.id)

        return payout

