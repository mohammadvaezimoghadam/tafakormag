import uuid
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import DonationTransaction, DonationCampaign


def initiate_donation(
    campaign_id,
    amount: int,
    is_anonymous: bool = False,
    donor=None
) -> tuple[DonationTransaction, str]:
    """
    Initiates a new donation transaction in PENDING status and returns the transaction
    along with the payment gateway redirect URL.
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

    authority = f"AUTH_{uuid.uuid4().hex}"
    
    trx = DonationTransaction.objects.create(
        campaign=campaign,
        donor=donor if donor and donor.is_authenticated else None,
        amount=amount,
        is_anonymous=is_anonymous,
        status=DonationTransaction.PaymentStatus.PENDING,
        authority=authority
    )

    # In production, this would call Shaparak/Zarinpal API to obtain authority and payment URL
    gateway_url = f"/api/v1/donations/payment/mock-gateway/?authority={authority}"
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
