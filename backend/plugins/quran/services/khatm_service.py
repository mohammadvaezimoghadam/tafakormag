"""
Business logic service for Quran Khatm campaigns and slot lifecycle management.
"""
import logging
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest
from django.utils import timezone

from plugins.quran.models import KhatmCampaign, KhatmSlot

logger = logging.getLogger(__name__)


def release_expired_khatm_slots() -> int:
    """
    Safely releases expired slot reservations back to the public pool.
    Prevents race conditions using conditional atomic updates (update only if still RESERVED).
    Uses Greatest() to prevent negative counts on reserved_units.
    """
    now = timezone.now()
    expired_slots = KhatmSlot.objects.filter(
        status=KhatmSlot.Status.RESERVED,
        expires_at__lt=now
    ).select_related('campaign')

    released_count = 0

    for slot in expired_slots:
        campaign = slot.campaign
        with transaction.atomic():
            # Lock campaign first to preserve lock ordering and eliminate deadlocks with API transactions
            KhatmCampaign.objects.select_for_update().filter(id=campaign.id).first()

            if campaign.unit_type in [KhatmCampaign.UnitType.JUZ, KhatmCampaign.UnitType.HIZB]:
                # Discrete slot: reset status to AVAILABLE
                updated = KhatmSlot.objects.filter(
                    id=slot.id,
                    status=KhatmSlot.Status.RESERVED,
                    expires_at__lt=now
                ).update(
                    status=KhatmSlot.Status.AVAILABLE,
                    user=None,
                    reserved_at=None,
                    expires_at=None
                )
                if updated:
                    KhatmCampaign.objects.filter(id=campaign.id).update(
                        reserved_units=Greatest(F('reserved_units') - slot.quantity, 0)
                    )
                    released_count += 1
                    logger.info(
                        "Released expired discrete slot %s (unit %s) in campaign %s",
                        slot.id, slot.unit_number, campaign.invite_code
                    )
            else:
                # Dynamic Surah slot: delete allocation
                deleted_count, _ = KhatmSlot.objects.filter(
                    id=slot.id,
                    status=KhatmSlot.Status.RESERVED,
                    expires_at__lt=now
                ).delete()

                if deleted_count > 0:
                    KhatmCampaign.objects.filter(id=campaign.id).update(
                        reserved_units=Greatest(F('reserved_units') - slot.quantity, 0)
                    )
                    released_count += 1
                    logger.info(
                        "Deleted expired surah slot %s (qty %s) in campaign %s",
                        slot.id, slot.quantity, campaign.invite_code
                    )

    return released_count


def expire_khatm_campaigns() -> int:
    """
    Marks active campaigns past their deadline as EXPIRED.
    """
    now = timezone.now()
    updated = KhatmCampaign.objects.filter(
        status=KhatmCampaign.Status.ACTIVE,
        deadline__isnull=False,
        deadline__lt=now
    ).update(status=KhatmCampaign.Status.EXPIRED)

    if updated:
        logger.info("Marked %d Khatm campaigns as expired past deadline", updated)

    return updated
