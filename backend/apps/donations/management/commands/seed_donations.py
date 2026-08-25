from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.notes.models import Topic, Post
from apps.donations.models import DonationCampaign


class Command(BaseCommand):
    help = 'Seeds initial sample donation campaigns into database'

    def handle(self, *args, **options):
        creator = User.objects.first()
        if not creator:
            creator = User.objects.create_user(phone='09121234567', first_name='مدیر', last_name='سامانه')
            self.stdout.write(f"Created default user: {creator.phone}")

        topic = Topic.objects.first()
        if not topic:
            topic = Topic.objects.create(
                name='پویش‌های خیریه و نیکوکاری',
                description='کانون جمع‌آوری کمک‌های مردمی و جهادی',
                created_by=creator
            )
            self.stdout.write(f"Created default topic: {topic.name}")

        campaigns_data = [
            {
                'title': 'تجهیز و شاداب‌سازی ۲ کلاس درس در دبستان روستای محروم',
                'description': 'خرید ۲۰ عدد نیمکت استاندارد، یک تخته هوشمند و رنگ‌آمیزی کامل کلاس‌ها جهت ایجاد محیطی پویا برای دانش‌آموزان منطقه محروم.',
                'category': DonationCampaign.CategoryChoices.EDUCATION,
                'target_amount': 85000000,
                'status': DonationCampaign.StatusChoices.ACTIVE
            },
            {
                'title': 'تامین سیستم گرمایشی و تهویه مسجد و حسینیه حضرت ولیعصر (عج)',
                'description': 'خرید و راه‌اندازی دستگاه پکیج و رادیاتور جهت تامین گرمایش سالن اصلی مسجد و جلسات قرآنی جوانان.',
                'category': DonationCampaign.CategoryChoices.MOSQUE,
                'target_amount': 60000000,
                'status': DonationCampaign.StatusChoices.ACTIVE
            },
            {
                'title': 'تامین هزینه درمان و جراحی کودک کم‌شنوا',
                'description': 'تامین هزینه‌های پیوند حلزون گوش و جلسات توانبخشی و گفتاردرمانی برای کودک نیازمند.',
                'category': DonationCampaign.CategoryChoices.HEALTH,
                'target_amount': 120000000,
                'status': DonationCampaign.StatusChoices.ACTIVE
            }
        ]

        created_count = 0
        for item in campaigns_data:
            campaign, created = DonationCampaign.objects.get_or_create(
                title=item['title'],
                defaults={
                    'topic': topic,
                    'creator': creator,
                    'description': item['description'],
                    'category': item['category'],
                    'target_amount': item['target_amount'],
                    'status': item['status'],
                    'is_public_donors_list': True
                }
            )
            if created:
                post = Post.objects.create(
                    topic=topic,
                    author=creator,
                    content=f"🤲 **پویش مهربانی: {campaign.title}**\n\n{campaign.description}\n\n🎯 مبلغ هدف: {campaign.target_amount:,} تومان"
                )
                campaign.post = post
                campaign.save(update_fields=['post'])
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} donation campaigns."))
