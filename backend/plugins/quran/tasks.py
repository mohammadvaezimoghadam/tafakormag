"""
Celery background tasks for Quran Plugin.
"""
import logging
from plugins.quran.services.khatm_service import (
    release_expired_khatm_slots,
    expire_khatm_campaigns,
)

logger = logging.getLogger(__name__)

# Try importing celery shared_task if celery is installed, else provide a plain function
try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func


@shared_task
def task_release_expired_khatm_slots():
    """
    Periodic task to release expired reserved Khatm slots.
    Recommended schedule: every 5 to 10 minutes.
    """
    logger.info("Executing task_release_expired_khatm_slots...")
    released = release_expired_khatm_slots()
    expired_campaigns = expire_khatm_campaigns()
    logger.info(
        "task_release_expired_khatm_slots finished: %d slots released, %d campaigns expired.",
        released, expired_campaigns
    )
    return {"released_slots": released, "expired_campaigns": expired_campaigns}
