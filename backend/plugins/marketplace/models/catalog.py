from django.db import models
from django.conf import settings
from .base import TimeStampedModel, MarketplaceBaseModel
from .location import City


class Category(TimeStampedModel):
    """
    Hierarchical catalog categories (e.g. Books -> Classic Literature).
    Supports unlimited nesting via self-referential parent key.
    """
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, verbose_name="اسلاگ دسته‌بندی")
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="دسته‌بندی والد"
    )
    icon = models.CharField(max_length=100, blank=True, default="", verbose_name="نام آیکون یا تصویر")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        db_table = "marketplace_categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["slug"], name="idx_category_slug"),
            models.Index(fields=["is_active"], name="idx_category_is_active"),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Item(MarketplaceBaseModel):
    """
    Core unified catalog product entity supporting sales, donations, physical and digital goods.
    """
    class DealType(models.TextChoices):
        SALE = "sale", "فروش نقدی"
        DONATION = "donation", "اهدای رایگان"

    class DeliveryType(models.TextChoices):
        PHYSICAL = "physical", "کالای فیزیکی (پستی)"
        DIGITAL = "digital", "فایل دیجیتال (دانلودی)"

    class Condition(models.TextChoices):
        NEW = "new", "نو و آکبند"
        LIKE_NEW = "like_new", "در حد نو"
        USED = "used", "دست دوم سالم"
        DAMAGED = "damaged", "دارای ایراد جزئی"

    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        AVAILABLE = "available", "موجود و آماده فروش/اهدا"
        RESERVED = "reserved", "رزرو موقت در سبد خرید/درگاه"
        COMPLETED = "completed", "تکمیل و واگذار شده"
        ARCHIVED = "archived", "بایگانی شده"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marketplace_items",
        verbose_name="فروشنده / اهداکننده"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="دسته‌بندی"
    )
    topic = models.ForeignKey(
        'notes.Topic',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="marketplace_items",
        verbose_name="تاپیک مرتبط در تفاخر"
    )

    title = models.CharField(max_length=255, verbose_name="عنوان کالا")
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, null=True, blank=True, verbose_name="اسلاگ یکتا")
    description = models.TextField(blank=True, default="", verbose_name="شرح کامل کالا")

    deal_type = models.CharField(
        max_length=20,
        choices=DealType.choices,
        default=DealType.SALE,
        verbose_name="نوع معامله (فروش یا اهدا)"
    )
    delivery_type = models.CharField(
        max_length=20,
        choices=DeliveryType.choices,
        default=DeliveryType.PHYSICAL,
        verbose_name="شیوه تحویل (فیزیکی یا دیجیتال)"
    )

    price = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name="قیمت پایه به تومان (برای اهدا ۰ است)"
    )
    discount_price = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="قیمت شگفت‌انگیز / تخفیف‌خورده"
    )
    discount_ends_at = models.DateTimeField(null=True, blank=True, verbose_name="پایان مهلت تخفیف")

    stock = models.PositiveIntegerField(default=1, verbose_name="موجودی انبار")
    is_unlimited_stock = models.BooleanField(default=False, verbose_name="موجودی نامحدود (مخصوص فایل دیجیتال)")

    condition = models.CharField(
        max_length=30,
        choices=Condition.choices,
        null=True,
        blank=True,
        verbose_name="وضعیت فیزیکی کالا"
    )
    city = models.ForeignKey(
        City,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="items",
        verbose_name="شهر مبدا ارسال"
    )
    weight_grams = models.PositiveIntegerField(default=0, verbose_name="وزن مرسوله به گرم")

    digital_file_key = models.CharField(max_length=500, blank=True, default="", verbose_name="کلید ذخیره‌سازی امن فایل دیجیتال")
    file_format = models.CharField(max_length=20, blank=True, default="", verbose_name="فرمت فایل (pdf, epub, mp3...)")
    file_size_mb = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="حجم فایل به مگابایت")

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="وضعیت انتشار"
    )
    reserved_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="مهلت رزرو موقت بانکی (جلوگیری از Race Condition)"
    )

    views_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    is_featured = models.BooleanField(default=False, verbose_name="کالای ویژه / منتخب")

    class Meta:
        db_table = "marketplace_items"
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["seller"], name="idx_item_seller"),
            models.Index(fields=["category"], name="idx_item_category"),
            models.Index(fields=["deal_type"], name="idx_item_deal_type"),
            models.Index(fields=["delivery_type"], name="idx_item_delivery_type"),
            models.Index(fields=["status"], name="idx_item_status"),
            models.Index(fields=["is_featured"], name="idx_item_featured"),
            models.Index(fields=["created_at"], name="idx_item_created_at"),
            models.Index(fields=["status", "deal_type", "-created_at"], name="idx_item_st_dl_cr"),
            models.Index(fields=["status", "delivery_type", "-created_at"], name="idx_item_st_del_cr"),
            models.Index(fields=["status", "category", "-created_at"], name="idx_item_st_cat_cr"),
            models.Index(fields=["status", "price"], name="idx_item_st_price"),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_deal_type_display()})"


class ItemImage(TimeStampedModel):
    """
    Multiple gallery images per item with a dedicated primary cover photo.
    """
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Item"
    )
    image_url = models.CharField(max_length=500, verbose_name="Image URL")
    is_cover = models.BooleanField(default=False, verbose_name="Cover Image")
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="Sort Order")

    class Meta:
        db_table = "marketplace_item_images"
        verbose_name = "Item Image"
        verbose_name_plural = "Item Images"
        ordering = ["-is_cover", "sort_order", "id"]
        indexes = [
            models.Index(fields=["item"], name="idx_item_image_item"),
        ]

    def __str__(self):
        return f"Image #{self.id} for {self.item.title}"


class BookDetail(models.Model):
    """
    Specialized 1-to-1 extension table for books, avoiding sparse nullable columns in Item table.
    """
    item = models.OneToOneField(
        Item,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="book_detail",
        verbose_name="Item"
    )
    isbn = models.CharField(max_length=20, null=True, blank=True, verbose_name="ISBN")
    author = models.CharField(max_length=150, verbose_name="Author")
    translator = models.CharField(max_length=150, blank=True, default="", verbose_name="Translator")
    publisher = models.CharField(max_length=150, blank=True, default="", verbose_name="Publisher")
    publication_year = models.IntegerField(null=True, blank=True, verbose_name="Publication Year")
    pages_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Pages Count")

    class Meta:
        db_table = "marketplace_book_details"
        verbose_name = "Book Detail"
        verbose_name_plural = "Book Details"
        indexes = [
            models.Index(fields=["author"], name="idx_book_author"),
            models.Index(fields=["publisher"], name="idx_book_publisher"),
            models.Index(fields=["isbn"], name="idx_book_isbn"),
        ]

    def __str__(self):
        return f"Book info: {self.author} - {self.publisher}"


class ItemAttribute(TimeStampedModel):
    """
    Lightweight Entity-Attribute-Value (EAV) key-value pairs for non-book physical/digital items.
    """
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name="Item"
    )
    attribute_key = models.CharField(max_length=50, verbose_name="Attribute Key")
    attribute_value = models.CharField(max_length=255, verbose_name="Attribute Value")

    class Meta:
        db_table = "marketplace_item_attributes"
        verbose_name = "Item Attribute"
        verbose_name_plural = "Item Attributes"
        constraints = [
            models.UniqueConstraint(fields=["item", "attribute_key"], name="unique_item_attribute_key")
        ]
        indexes = [
            models.Index(fields=["attribute_key"], name="idx_attribute_key"),
        ]

    def __str__(self):
        return f"{self.attribute_key}: {self.attribute_value}"
