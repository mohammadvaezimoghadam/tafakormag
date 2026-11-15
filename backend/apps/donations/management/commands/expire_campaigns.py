"""
Management command to expire donation campaigns past their deadline.
Run via cron or Celery beat: python manage.py expire_campaigns
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.donations.models import DonationCampaign

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'انقضای خودکار پویش‌های اهدایی که مهلت‌شان گذشته — اجرا از طریق cron یا Celery beat'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='فقط تعداد پویش‌های منقضی‌شدنی را نمایش بده (بدون تغییر)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        expired_qs = DonationCampaign.objects.filter(
            status=DonationCampaign.StatusChoices.ACTIVE,
            deadline__isnull=False,
            deadline__lt=now,
        )

        count = expired_qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('هیچ پویش منقضی‌شدنی یافت نشد.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'[DRY RUN] {count} پویش با مهلت گذشته یافت شد (بدون تغییر):'
            ))
            for c in expired_qs.values_list('id', 'title', 'deadline'):
                self.stdout.write(f'  - {c[1]} (deadline={c[2]}, id={c[0]})')
            return

        updated = expired_qs.update(status=DonationCampaign.StatusChoices.EXPIRED)
        msg = f'{updated} پویش منقضی شد.'
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info('expire_campaigns: %s', msg)
