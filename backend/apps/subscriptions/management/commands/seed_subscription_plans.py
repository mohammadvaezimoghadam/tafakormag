from django.core.management.base import BaseCommand
from apps.subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'ایجاد و به‌روزرسانی طرح‌های پیش‌فرض اشتراک قرآن و افزونه‌ها'

    def handle(self, *args, **options):
        plans_data = [
            {
                'plugin_identifier': 'quran',
                'sku': 'sub_vip_1m',
                'title': 'اشتراک ۱ ماهه ویژه قرآن',
                'description': 'دسترسی نامحدود به تمام قاریان برجسته و ترجمه گویای صوتی به مدت ۳۰ روز',
                'duration_days': 30,
                'price': 390000,  # ۳۹,۰۰۰ تومان (به ریال)
                'features': {
                    'all_reciters': True,
                    'audio_translation': True,
                    'offline_download': True,
                },
                'is_active': True,
            },
            {
                'plugin_identifier': 'quran',
                'sku': 'sub_vip_3m',
                'title': 'اشتراک ۳ ماهه ویژه قرآن (فصلی)',
                'description': 'دسترسی نامحدود برای یک فصل همراه با ۲۵٪ تخفیف',
                'duration_days': 90,
                'price': 890000,  # ۸۹,۰۰۰ تومان (به ریال)
                'features': {
                    'all_reciters': True,
                    'audio_translation': True,
                    'offline_download': True,
                    'discount_badge': '۲۵٪ تخفیف',
                },
                'is_active': True,
            },
            {
                'plugin_identifier': 'quran',
                'sku': 'sub_vip_6m',
                'title': 'اشتراک ۶ ماهه ویژه قرآن (طلایی)',
                'description': 'محبوب‌ترین و به‌صرفه‌ترین پلن با دسترسی نامحدود برای ۱۸۰ روز همراه با تخفیف ویژه',
                'duration_days': 180,
                'price': 1490000,  # ۱۴۹,۰۰۰ تومان (به ریال)
                'features': {
                    'all_reciters': True,
                    'audio_translation': True,
                    'offline_download': True,
                    'discount_badge': '۴۰٪ تخفیف ویژه',
                    'is_recommended': True,
                },
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for p_data in plans_data:
            sku = p_data.pop('sku')
            plan, created = SubscriptionPlan.objects.update_or_create(
                sku=sku,
                defaults=p_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ پلن جدید ساخته شد: {plan.title} ({sku})"))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"🔄 پلن به‌روزرسانی شد: {plan.title} ({sku})"))

        self.stdout.write(self.style.SUCCESS(
            f"عملیات ثبت پلن‌ها پایان یافت. ساخت: {created_count}، به‌روزرسانی: {updated_count}"
        ))

