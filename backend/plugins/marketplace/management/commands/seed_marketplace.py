from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from plugins.marketplace.models.location import Province, City
from plugins.marketplace.models.catalog import Category, Item, BookDetail
from plugins.marketplace.models.finance import SellerBankAccount
from plugins.marketplace.models.discount import Coupon

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial data for Tafakor Marketplace. By default seeds only Master Reference Data (Provinces, Categories). Pass --demo for sample items & coupons."

    def add_arguments(self, parser):
        parser.add_argument(
            "--demo",
            action="store_true",
            help="Seed sample books, mock seller bank account, and demo coupons (FOR LOCAL DEV ONLY)",
        )

    def handle(self, *args, **options):
        is_demo = options.get("demo", False)
        self.stdout.write(self.style.NOTICE("🌱 Starting Marketplace seeding routine..."))

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
        tehran_city = None
        for prov_name, city_list in provinces_data.items():
            province, _ = Province.objects.get_or_create(name=prov_name)
            for city_name in city_list:
                city, created = City.objects.get_or_create(province=province, name=city_name)
                if prov_name == "تهران" and city_name == "تهران":
                    tehran_city = city
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

        cat_map = {}
        for name, slug, order in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "order": order, "is_active": True}
            )
            cat_map[slug] = cat

        self.stdout.write(self.style.SUCCESS(f"  ✓ Seeded {len(cat_map)} primary marketplace categories."))

        if not is_demo:
            self.stdout.write(self.style.NOTICE("  ℹ Demo books & coupons skipped. Pass '--demo' to seed sample catalog items for local development."))
            self.stdout.write(self.style.SUCCESS("🎉 Master Reference Data seeding completed successfully!"))
            return

        # 3. Retrieve or create primary seller for local development demo
        seller = User.objects.filter(is_superuser=True).first()
        if not seller:
            seller = User.objects.first()

        if not seller:
            seller = User.objects.create_superuser(phone="09019227853", password="password123")

        # 4. Seed Verified Bank Account for Seller
        SellerBankAccount.objects.get_or_create(
            user=seller,
            iban="IR120170000000123456789012",
            defaults={
                "bank_name": "بانک ملی ایران",
                "account_holder_name": seller.get_full_name() or "مدیر بازارچه تفاخر",
                "is_verified": True,
                "is_default": True,
            }
        )

        # 5. Seed Diverse Sample Books / Items
        sample_items = [
            {
                "title": "دیوان حافظ شیرازی (نسخه نفیس خطی)",
                "slug": "divan-hafez-nafis",
                "category": cat_map["literature-poetry"],
                "deal_type": Item.DealType.SALE,
                "delivery_type": Item.DeliveryType.PHYSICAL,
                "price": Decimal("280000"),
                "discount_price": Decimal("220000"),
                "discount_ends_at": timezone.now() + timedelta(days=30),
                "stock": 8,
                "condition": Item.Condition.NEW,
                "is_featured": True,
                "weight_grams": 750,
                "description": "چاپ نفیس با خط استاد خوشنویسی، کاغذ گلاسه معطر، جلد چرم گالینگور زرکوب همراه با قاب اختصاصی.",
                "book_detail": {
                    "author": "خواجه شمس‌الدین محمد حافظ شیرازی",
                    "publisher": "انتشارات ققنوس",
                    "isbn": "978-964-311-542-1",
                    "pages_count": 520,
                    "publication_year": 1402,
                }
            },
            {
                "title": "کتاب الکترونیکی تفسیر نمونه (دوره کامل ۲۷ جلدی)",
                "slug": "tafsir-nemooneh-ebook",
                "category": cat_map["religious-books"],
                "deal_type": Item.DealType.SALE,
                "delivery_type": Item.DeliveryType.DIGITAL,
                "price": Decimal("120000"),
                "discount_price": Decimal("85000"),
                "stock": 1,
                "is_unlimited_stock": True,
                "is_featured": True,
                "file_format": "PDF / EPUB",
                "file_size_mb": Decimal("48.5"),
                "digital_file_key": "samples/tafsir_sample.pdf",
                "description": "دوره کامل تفسیر نمونه به قلم آیت‌الله مکارم شیرازی و جمعی از دانشمندان، با قابلیت جستجوی تمام‌متن.",
                "book_detail": {
                    "author": "آیت‌الله ناصر مکارم شیرازی",
                    "publisher": "دار الکتب الاسلامیه",
                    "isbn": "978-964-440-101-9",
                    "pages_count": 9800,
                    "publication_year": 1401,
                }
            },
            {
                "title": "مفاتیح الجنان (طرح اهدای کتاب)",
                "slug": "mafatih-al-jinan-donation",
                "category": cat_map["religious-books"],
                "deal_type": Item.DealType.DONATION,
                "delivery_type": Item.DeliveryType.PHYSICAL,
                "price": Decimal("0"),
                "stock": 15,
                "condition": Item.Condition.LIKE_NEW,
                "is_featured": False,
                "weight_grams": 600,
                "description": "اهدای رایگان جهت ترویج فرهنگ مطالعه دینی به طلاب، دانشجویان و مساجد متقاضی در سراسر کشور. هزینه ارسال با گیرنده است.",
                "book_detail": {
                    "author": "شیخ عباس قمی",
                    "publisher": "انتشارات اسوه",
                    "isbn": "978-964-880-330-4",
                    "pages_count": 850,
                    "publication_year": 1400,
                }
            },
            {
                "title": "ریاضیات پایه و حساب دیفرانسیل دانشگاهی",
                "slug": "university-calculus",
                "category": cat_map["academic-books"],
                "deal_type": Item.DealType.SALE,
                "delivery_type": Item.DeliveryType.PHYSICAL,
                "price": Decimal("195000"),
                "stock": 4,
                "condition": Item.Condition.USED,
                "weight_grams": 800,
                "description": "منبع رسمی درس ریاضی عمومی ۱ و ۲ برای کلیه رشته‌های مهندسی و علوم پایه. کاملاً سالم و تمیز.",
                "book_detail": {
                    "author": "جیمز استوارت",
                    "translator": "دکتر علی‌اکبر عالم‌زاده",
                    "publisher": "انتشارات علمی و فنی",
                    "isbn": "978-964-620-004-8",
                    "pages_count": 640,
                    "publication_year": 1399,
                }
            },
        ]

        for item_data in sample_items:
            book_meta = item_data.pop("book_detail")
            item_slug = item_data.pop("slug")
            item, _ = Item.objects.get_or_create(
                slug=item_slug,
                defaults={
                    **item_data,
                    "seller": seller,
                    "city": tehran_city,
                    "status": Item.Status.AVAILABLE,
                }
            )
            BookDetail.objects.get_or_create(item=item, defaults=book_meta)

        self.stdout.write(self.style.SUCCESS(f"  ✓ Seeded {len(sample_items)} diverse catalog books."))

        # 6. Seed Discount Coupons
        coupons = [
            {
                "code": "TAFAKOR20",
                "title": "تخفیف ویژه ۲۰ درصدی افتتاحیه بازارچه",
                "discount_type": Coupon.DiscountType.PERCENTAGE,
                "discount_value": Decimal("20"),
                "max_discount_amount": Decimal("60000"),
                "min_order_amount": Decimal("100000"),
                "valid_from": timezone.now() - timedelta(days=1),
                "valid_until": timezone.now() + timedelta(days=90),
                "is_active": True,
            },
            {
                "code": "BOOK50",
                "title": "تخفیف نقدی ۵۰ هزار تومانی کتابخوانی",
                "discount_type": Coupon.DiscountType.FIXED_AMOUNT,
                "discount_value": Decimal("50000"),
                "min_order_amount": Decimal("150000"),
                "valid_from": timezone.now() - timedelta(days=1),
                "valid_until": timezone.now() + timedelta(days=60),
                "is_active": True,
            },
        ]

        for c in coupons:
            code = c.pop("code")
            Coupon.objects.get_or_create(code=code, defaults=c)

        self.stdout.write(self.style.SUCCESS(f"  ✓ Seeded {len(coupons)} discount coupons (TAFAKOR20, BOOK50)."))
        self.stdout.write(self.style.SUCCESS("🎉 Marketplace seeding completed successfully!"))
