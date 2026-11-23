"""
Management command to release expired Khatm slot reservations and expire past-deadline campaigns.
Can be executed via Cron, Celery beat, or direct CLI.
Usage: python manage.py release_expired_khatms [--dry-run]
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from plugins.quran.models import KhatmSlot, KhatmCampaign
from plugins.quran.services.khatm_service import (
    release_expired_khatm_slots,
    expire_khatm_campaigns,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'آزادسازی سهم‌های منقضی‌شده ختم گروهی و به‌روزرسانی پویش‌های گذشته از مهلت'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='تنها نمایش تعداد سهم‌ها و پویش‌های منقضی بدون اعمال تغییر',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        expired_slots_qs = KhatmSlot.objects.filter(
            status=KhatmSlot.Status.RESERVED,
            expires_at__lt=now,
        )
        expired_campaigns_qs = KhatmCampaign.objects.filter(
            status=KhatmCampaign.Status.ACTIVE,
            deadline__isnull=False,
            deadline__lt=now,
        )

        slots_count = expired_slots_qs.count()
        campaigns_count = expired_campaigns_qs.count()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"[DRY RUN] {slots_count} سهم منقضی و {campaigns_count} پویش با مهلت گذشته یافت شد."
            ))
            return

        released = release_expired_khatm_slots()
        expired = expire_khatm_campaigns()

        self.stdout.write(self.style.SUCCESS(
            f"عملیات با موفقیت انجام شد: {released} سهم آزاد شد و {expired} پویش منقضی گردید."
        ))
