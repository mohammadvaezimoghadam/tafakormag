from django.core.management.base import BaseCommand
from apps.ota.models import App, BaseRelease


class Command(BaseCommand):
    help = "Seeds initial OTA apps and base releases (tafakor_shop, quran_tafakor)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🌱 Starting OTA App seeding..."))

        # 1. Seed or update tafakor_shop
        shop_app, created = App.objects.get_or_create(
            app_id="tafakor_shop",
            defaults={
                "name": "فروشگاه و گردش کتاب تفکر",
                "package_name": "com.example.tafakor_shop",
                "platform": "android",
                "description": "اپلیکیشن فروشگاهی، گردش فیزیکی کتاب و کیوسک هوشمند تفکر",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("  ✓ Created App: tafakor_shop"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ App tafakor_shop already exists."))

        # 2. Seed BaseRelease for tafakor_shop
        base_rel, rel_created = BaseRelease.objects.get_or_create(
            app=shop_app,
            release_name="1.0.0+1",
            defaults={
                "build_number": 1,
                "version_string": "1.0.0",
                "store_url": "bazaar://details?id=com.example.tafakor_shop",
                "store_web_url": "https://cafebazaar.ir/app/com.example.tafakor_shop",
                "is_active": True,
            }
        )
        if rel_created:
            self.stdout.write(self.style.SUCCESS("  ✓ Created BaseRelease: 1.0.0+1 for tafakor_shop"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ BaseRelease 1.0.0+1 already exists."))

        self.stdout.write(self.style.SUCCESS("🎉 OTA Seeding completed successfully!"))
