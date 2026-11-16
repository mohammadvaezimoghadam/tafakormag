from django.core.management.base import BaseCommand
from apps.marketplace.models.location import Province, City
from apps.marketplace.models.catalog import Category


class Command(BaseCommand):
    help = "Seeds initial reference data for Tafakor Marketplace (Provinces, Cities, and Master Categories)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🌱 Starting Marketplace reference data seeding..."))

        # 1. Seed Provinces & Major Cities
        provinces_data = {
            "تهران": ["تهران", "ری", "شهریار", "دماوند"],
            "خراسان رضوی": ["مشهد", "نیشابور", "سبزوار"],
            "اصفهان": ["اصفهان", "کاشان", "نجف‌آباد"],
            "فارس": ["شیراز", "مرودشت", "کازرون"],
            "قم": ["قم"],
            "مازندران": ["ساری", "بابل", "آمل"],
            "آذربایجان شرقی": ["تبریز", "مراغه"],
        }

        cities_count = 0
        for prov_name, city_list in provinces_data.items():
            province, _ = Province.objects.get_or_create(name=prov_name)
            for city_name in city_list:
                _, created = City.objects.get_or_create(province=province, name=city_name)
                if created:
                    cities_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ Seeded {len(provinces_data)} provinces and {cities_count} cities."))

        # 2. Seed Master Categories
        categories_data = [
            ("کتب مذهبی و معارف اسلامی", "religious-books", 1),
            ("ادبیات، شعر و رمان", "literature-poetry", 2),
            ("کتب دانشگاهی و کنکور", "academic-books", 3),
            ("تاریخ، فلسفه و علوم انسانی", "history-philosophy", 4),
            ("نرم‌افزار و محتوای چندرسانه‌ای", "multimedia-software", 5),
            ("کتب کودک و نوجوان", "children-books", 6),
        ]

        for name, slug, order in categories_data:
            Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "order": order, "is_active": True}
            )

        self.stdout.write(self.style.SUCCESS(f"  ✓ Seeded {len(categories_data)} primary marketplace categories."))
        self.stdout.write(self.style.SUCCESS("🎉 Master Reference Data seeding completed successfully!"))
