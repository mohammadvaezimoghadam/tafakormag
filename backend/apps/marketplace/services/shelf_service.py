from datetime import timedelta
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..exceptions import InvalidShelfTransitionError, ShelfBookError
from ..models.catalog import BookDetail, Category, Item
from ..models.circulation import BookStation, BookTitle, PhysicalCopy, Transfer
from ..models.donation import Donation
from ..models.location import City
from ..models.shelf import UserShelfBook
from .circulation_service import CirculationService

logger = logging.getLogger(__name__)
User = get_user_model()


_PHYSICAL_TO_ITEM_CONDITION_MAP = {
    PhysicalCopy.Condition.NEW: Item.Condition.NEW,
    PhysicalCopy.Condition.LIKE_NEW: Item.Condition.LIKE_NEW,
    PhysicalCopy.Condition.GOOD: Item.Condition.USED,
    PhysicalCopy.Condition.FAIR: Item.Condition.USED,
    PhysicalCopy.Condition.WORN: Item.Condition.DAMAGED,
}


class ShelfService:
    """
    Domain service managing users' personal book shelves (قفسه کتاب من)
    and optional transitions into QR circulation, C2C donation, or sale.
    """

    @staticmethod
    def _assert_owner(user, shelf_book: UserShelfBook) -> None:
        if not user or not user.is_authenticated or shelf_book.user_id != user.id:
            raise ShelfBookError("شما اجازه ویرایش یا مدیریت این کتاب را ندارید.")

    @staticmethod
    def _validate_rating(rating: Optional[int]) -> Optional[int]:
        if rating is None:
            return None
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ShelfBookError("امتیاز کتاب باید عددی بین ۱ تا ۵ باشد.")
        return rating

    @staticmethod
    def _validate_quantity(quantity: Any, min_value: int = 1) -> int:
        try:
            parsed = int(quantity)
        except (TypeError, ValueError):
            raise ShelfBookError("تعداد جلد کتاب باید یک عدد صحیح معتبر باشد.")
        if parsed < min_value or parsed > 10000:
            raise ShelfBookError(f"تعداد جلد کتاب باید بین {min_value} تا ۱۰۰۰۰ باشد.")
        return parsed

    @staticmethod
    def _resolve_book_title(user, data: Dict[str, Any]) -> BookTitle:
        book_title_id = data.get("book_title_id")
        if book_title_id:
            book_title = BookTitle.objects.filter(id=book_title_id).first()
            if not book_title:
                raise ShelfBookError("عنوان کتاب انتخاب‌شده یافت نشد.")
            return book_title

        title = (data.get("title") or "").strip()
        author = (data.get("author") or "").strip()
        if not title or not author:
            raise ShelfBookError("در صورت عدم انتخاب از کاتالوگ، عنوان کتاب و نام نویسنده الزامی است.")

        return CirculationService.register_book_title(user=user, data=data)

    @staticmethod
    def _resolve_marketplace_category(category_id: Optional[int]) -> Category:
        if category_id:
            category = Category.objects.filter(id=category_id, is_active=True).first()
            if not category:
                raise ShelfBookError("دسته‌بندی انتخاب‌شده معتبر نیست.")
            return category

        category = Category.objects.filter(is_active=True).order_by("order", "id").first()
        if category:
            return category

        fallback, _ = Category.objects.get_or_create(
            slug="other-books",
            defaults={"name": "سایر کتاب‌ها", "order": 99, "is_active": True},
        )
        return fallback

    @staticmethod
    def _ensure_withdrawable_copy(user, shelf_book: UserShelfBook) -> None:
        """Checks whether linked circulation/marketplace entities can safely be withdrawn."""
        copy = shelf_book.physical_copy
        if copy:
            if copy.current_holder_id != user.id:
                raise InvalidShelfTransitionError(
                    "این جلد فیزیکی به خواننده دیگری منتقل شده است و امکان بازگرداندن آن وجود ندارد."
                )
            if copy.status == PhysicalCopy.Status.TRANSFERRING:
                raise InvalidShelfTransitionError(
                    "این کتاب هم‌اکنون در حال انتقال حضوری است. ابتدا انتقال جاری را تکمیل یا لغو کنید."
                )
            if copy.status == PhysicalCopy.Status.IN_STATION:
                raise InvalidShelfTransitionError(
                    "این کتاب هم‌اکنون در قفسه عمومی تفاخر قرار دارد و نزد شما نیست."
                )

        item = shelf_book.marketplace_item
        if item and not item.is_deleted:
            if item.status == Item.Status.RESERVED:
                raise InvalidShelfTransitionError(
                    "این کتاب هم‌اکنون در حال تسویه بانکی یا رزرو خریدار است و قابل تغییر نیست."
                )
            if item.status == Item.Status.COMPLETED:
                raise InvalidShelfTransitionError(
                    "این کتاب قبلاً واگذار یا فروخته شده است."
                )

    @classmethod
    @transaction.atomic
    def add_book(cls, user, data: Dict[str, Any]) -> UserShelfBook:
        """Registers a new personal book onto the authenticated user's shelf."""
        if not user or not user.is_authenticated:
            raise ShelfBookError("برای ثبت کتاب در قفسه، ورود به حساب کاربری الزامی است.")

        book_title = cls._resolve_book_title(user=user, data=data)
        rating = cls._validate_rating(data.get("rating"))
        quantity = cls._validate_quantity(
            1 if data.get("quantity") is None else data.get("quantity"),
            min_value=1,
        )

        book_format = data.get("book_format", UserShelfBook.BookFormat.PHYSICAL)
        condition = data.get("condition")
        if book_format == UserShelfBook.BookFormat.DIGITAL:
            condition = None
        elif not condition:
            condition = PhysicalCopy.Condition.GOOD

        entry = UserShelfBook.objects.create(
            user=user,
            book_title=book_title,
            book_format=book_format,
            visibility=UserShelfBook.Visibility.PRIVATE,
            reading_status=data.get("reading_status", UserShelfBook.ReadingStatus.IN_SHELF),
            disposition=UserShelfBook.Disposition.KEEPING,
            condition=condition,
            quantity=quantity,
            personal_note=(data.get("personal_note") or "").strip(),
            digital_reference=(data.get("digital_reference") or "").strip(),
            acquired_from=(data.get("acquired_from") or "").strip(),
            rating=rating,
        )
        cover_image = data.get("cover_image")
        if cover_image and not book_title.cover_image:
            book_title.cover_image = cover_image
            book_title.save(update_fields=["cover_image", "updated_at"])

        logger.info("Shelf book created: id=%s user=%s title=%s", entry.id, user.id, book_title.id)
        return entry

    @classmethod
    @transaction.atomic
    def update_book(cls, user, shelf_book: UserShelfBook, data: Dict[str, Any]) -> UserShelfBook:
        """Updates personal shelf fields such as reading status, format, and notes."""
        cls._assert_owner(user, shelf_book)

        new_format = data.get("book_format", shelf_book.book_format)
        if (
            new_format == UserShelfBook.BookFormat.DIGITAL
            and shelf_book.disposition == UserShelfBook.Disposition.CIRCULATING
        ):
            raise InvalidShelfTransitionError(
                "کتابی که در گردش فیزیکی قرار دارد نمی‌تواند به نسخه دیجیتال تغییر یابد."
            )

        if "rating" in data:
            shelf_book.rating = cls._validate_rating(data.get("rating"))

        if "quantity" in data and data.get("quantity") is not None:
            shelf_book.quantity = cls._validate_quantity(data.get("quantity"), min_value=1)

        for field in (
            "book_format",
            "reading_status",
            "condition",
        ):
            if field in data:
                setattr(shelf_book, field, data[field])

        shelf_book.visibility = UserShelfBook.Visibility.PRIVATE

        for text_field in ("personal_note", "digital_reference", "acquired_from"):
            if text_field in data:
                setattr(shelf_book, text_field, (data[text_field] or "").strip())

        if shelf_book.book_format == UserShelfBook.BookFormat.DIGITAL:
            shelf_book.condition = None

        if "cover_image" in data:
            shelf_book.book_title.cover_image = data["cover_image"]
            shelf_book.book_title.save(update_fields=["cover_image", "updated_at"])

        linked_item = shelf_book.marketplace_item
        if (
            linked_item
            and not linked_item.is_deleted
            and linked_item.status == Item.Status.AVAILABLE
            and shelf_book.book_format == UserShelfBook.BookFormat.PHYSICAL
            and linked_item.stock > shelf_book.quantity
        ):
            linked_item.stock = shelf_book.quantity
            linked_item.save(update_fields=["stock", "updated_at"])

        shelf_book.save()
        return shelf_book

    @classmethod
    @transaction.atomic
    def remove_book(cls, user, shelf_book: UserShelfBook) -> None:
        """
        Soft-deletes a shelf book after verifying no active checkout/handover locks it
        and archiving any active marketplace offering.
        """
        cls._assert_owner(user, shelf_book)
        cls._ensure_withdrawable_copy(user, shelf_book)

        if shelf_book.disposition != UserShelfBook.Disposition.KEEPING:
            cls._archive_active_offerings(shelf_book)

        shelf_book.delete()
        logger.info("Shelf book soft-deleted: id=%s user=%s", shelf_book.id, user.id)

    @staticmethod
    def _archive_active_offerings(shelf_book: UserShelfBook) -> None:
        copy = shelf_book.physical_copy
        if copy and copy.status == PhysicalCopy.Status.ACTIVE:
            copy.status = PhysicalCopy.Status.RETIRED
            copy.save(update_fields=["status", "updated_at"])

        item = shelf_book.marketplace_item
        if item and not item.is_deleted and item.status in (Item.Status.AVAILABLE, Item.Status.DRAFT):
            item.status = Item.Status.ARCHIVED
            item.save(update_fields=["status", "updated_at"])

    @classmethod
    @transaction.atomic
    def start_circulation(
        cls,
        user,
        shelf_book: UserShelfBook,
        condition: Optional[str] = None,
        privacy: str = PhysicalCopy.Privacy.FIRST_NAME_ONLY,
    ) -> UserShelfBook:
        """
        Enrolls a physical shelf book into QR circulation (PhysicalCopy).
        Reuses and reactivates an existing retired copy owned by the user if present.
        """
        cls._assert_owner(user, shelf_book)

        if shelf_book.book_format != UserShelfBook.BookFormat.PHYSICAL:
            raise InvalidShelfTransitionError(
                "گردش حضوری و دریافت کد QR فقط برای کتاب‌های فیزیکی امکان‌پذیر است."
            )
        if shelf_book.quantity < 1:
            raise InvalidShelfTransitionError(
                "موجودی این کتاب در قفسه صفر است؛ ابتدا تعداد کتاب را افزایش دهید."
            )

        if shelf_book.marketplace_item and not shelf_book.marketplace_item.is_deleted:
            if shelf_book.marketplace_item.status == Item.Status.RESERVED:
                raise InvalidShelfTransitionError(
                    "این کتاب هم‌اکنون در بازارچه رزرو شده است."
                )
            if shelf_book.marketplace_item.status == Item.Status.COMPLETED:
                raise InvalidShelfTransitionError(
                    "این کتاب قبلاً در بازارچه واگذار یا فروخته شده است."
                )
            if shelf_book.marketplace_item.status == Item.Status.AVAILABLE:
                shelf_book.marketplace_item.status = Item.Status.ARCHIVED
                shelf_book.marketplace_item.save(update_fields=["status", "updated_at"])

        resolved_condition = condition or shelf_book.condition or PhysicalCopy.Condition.GOOD
        copy = shelf_book.physical_copy

        if copy:
            if copy.current_holder_id != user.id:
                raise InvalidShelfTransitionError(
                    "این نسخه فیزیکی هم‌اکنون نزد کاربر دیگری است."
                )
            if copy.status == PhysicalCopy.Status.IN_STATION:
                raise InvalidShelfTransitionError(
                    "این کتاب هم‌اکنون در قفسه عمومی تفاخر قرار دارد."
                )
            if copy.status != PhysicalCopy.Status.ACTIVE:
                copy.status = PhysicalCopy.Status.ACTIVE
            copy.condition = resolved_condition
            copy.privacy = privacy
            copy.save(update_fields=["status", "condition", "privacy", "updated_at"])
        else:
            copy = CirculationService.register_physical_copy(
                user=user,
                book_title_id=shelf_book.book_title_id,
                condition=resolved_condition,
                privacy=privacy,
            )
            shelf_book.physical_copy = copy

        shelf_book.condition = resolved_condition
        shelf_book.disposition = UserShelfBook.Disposition.CIRCULATING
        shelf_book.donation_methods = [Item.DonationMethod.IN_PERSON]
        shelf_book.save(update_fields=["physical_copy", "condition", "disposition", "donation_methods", "updated_at"])
        logger.info("Shelf book %s entered QR circulation as %s", shelf_book.id, copy.short_code)
        return shelf_book

    @classmethod
    @transaction.atomic
    def publish_to_marketplace(cls, user, shelf_book: UserShelfBook, data: Dict[str, Any]) -> UserShelfBook:
        """
        Publishes (or updates) a shelf book onto the C2C Marketplace as a DONATION or SALE Item,
        preserving or issuing PhysicalCopy QR circulation for in-person/station book donations
        and automatically syncing BookDetail and BookTitle links.
        """
        cls._assert_owner(user, shelf_book)

        deal_type = data.get("deal_type")
        if deal_type not in (Item.DealType.DONATION, Item.DealType.SALE):
            raise InvalidShelfTransitionError("نوع عرضه باید یکی از دو حالت اهدا یا فروش باشد.")

        copy = shelf_book.physical_copy
        if deal_type == Item.DealType.SALE or (copy and copy.status == PhysicalCopy.Status.TRANSFERRING):
            cls._ensure_withdrawable_copy(user, shelf_book)
        elif shelf_book.marketplace_item and not shelf_book.marketplace_item.is_deleted:
            if shelf_book.marketplace_item.status in (Item.Status.RESERVED, Item.Status.COMPLETED):
                cls._ensure_withdrawable_copy(user, shelf_book)

        price = Decimal(str(data.get("price") or 0))
        if deal_type == Item.DealType.DONATION:
            price = Decimal("0")
        elif price <= 0:
            raise InvalidShelfTransitionError("برای قرار دادن کتاب در حالت فروش، درج قیمت معتبر الزامی است.")

        category = cls._resolve_marketplace_category(data.get("category_id"))

        city = None
        city_id = data.get("city_id")
        if city_id:
            city = City.objects.filter(id=city_id).first()
            if not city:
                raise ShelfBookError("شهر انتخاب‌شده معتبر نیست.")

        delivery_type = (
            Item.DeliveryType.DIGITAL
            if shelf_book.book_format == UserShelfBook.BookFormat.DIGITAL
            else Item.DeliveryType.PHYSICAL
        )
        if shelf_book.quantity < 1:
            raise InvalidShelfTransitionError(
                "موجودی این کتاب در قفسه صفر است؛ ابتدا تعداد کتاب را در قفسه افزایش دهید."
            )
        item_condition = (
            None
            if delivery_type == Item.DeliveryType.DIGITAL
            else _PHYSICAL_TO_ITEM_CONDITION_MAP.get(shelf_book.condition or PhysicalCopy.Condition.GOOD, Item.Condition.USED)
        )
        raw_stock = data.get("stock")
        stock = cls._validate_quantity(1 if raw_stock is None else raw_stock, min_value=1)
        if delivery_type == Item.DeliveryType.PHYSICAL and stock > shelf_book.quantity:
            raise InvalidShelfTransitionError(
                f"تعداد انتخاب‌شده ({stock} جلد) از موجودی قفسه شما ({shelf_book.quantity} جلد) بیشتر است."
            )
        description = (data.get("description") or shelf_book.book_title.description or "").strip()
        weight_grams = 0 if delivery_type == Item.DeliveryType.DIGITAL else int(data.get("weight_grams") or 0)

        station = None
        station_id = data.get("station_id")
        if station_id:
            station = BookStation.objects.filter(id=station_id, is_active=True).first()
            if not station:
                raise ShelfBookError("ایستگاه یا قفسه تفاخر انتخاب‌شده یافت نشد یا فعال نیست.")

        donation_methods: list[str] = []
        shipping_payer = data.get("shipping_payer") or shelf_book.shipping_payer or Donation.ShippingPayer.RECIPIENT
        if shipping_payer not in (Donation.ShippingPayer.RECIPIENT, Donation.ShippingPayer.DONOR):
            shipping_payer = Donation.ShippingPayer.RECIPIENT

        linked_copy = None
        if deal_type == Item.DealType.DONATION:
            raw_methods = data.get("donation_methods")
            donation_methods = Item.normalize_donation_methods(
                raw_methods if raw_methods is not None else shelf_book.donation_methods,
                delivery_type=delivery_type,
                has_station=bool(station),
                has_physical_copy=False,
            )
            deposit_now = bool(data.get("deposit_now"))
            if deposit_now and not station:
                raise ShelfBookError("برای ثبت فوری در ایستگاه، انتخاب یک ایستگاه تفاخر الزامی است.")

            needs_qr_copy = (
                delivery_type == Item.DeliveryType.PHYSICAL
                and (Item.DonationMethod.IN_PERSON in donation_methods or deposit_now)
            )
            if needs_qr_copy:
                resolved_condition = shelf_book.condition or PhysicalCopy.Condition.GOOD
                if copy:
                    if copy.status == PhysicalCopy.Status.IN_STATION:
                        if not (station and copy.station_id == station.id):
                            raise InvalidShelfTransitionError("این کتاب هم‌اکنون در قفسه عمومی دیگری قرار دارد.")
                    elif copy.current_holder_id != user.id:
                        raise InvalidShelfTransitionError("این نسخه فیزیکی هم‌اکنون نزد کاربر دیگری است.")
                    elif copy.status != PhysicalCopy.Status.ACTIVE:
                        copy.status = PhysicalCopy.Status.ACTIVE
                        copy.condition = resolved_condition
                        copy.privacy = data.get("privacy") or copy.privacy or PhysicalCopy.Privacy.FIRST_NAME_ONLY
                        copy.save(update_fields=["status", "condition", "privacy", "updated_at"])
                else:
                    copy = CirculationService.register_physical_copy(
                        user=user,
                        book_title_id=shelf_book.book_title_id,
                        condition=resolved_condition,
                        privacy=data.get("privacy") or PhysicalCopy.Privacy.FIRST_NAME_ONLY,
                    )
                    shelf_book.physical_copy = copy

                if deposit_now and station and copy.status != PhysicalCopy.Status.IN_STATION:
                    copy, _ = CirculationService.deposit_to_station(
                        user=user,
                        short_code=copy.short_code,
                        station_id=station.id,
                        donor_note=description[:300],
                    )
                linked_copy = copy
            elif copy and copy.status == PhysicalCopy.Status.ACTIVE:
                copy.status = PhysicalCopy.Status.RETIRED
                copy.save(update_fields=["status", "updated_at"])
        else:
            # Sale listing: cleanly retire held active QR copy and clear donation-only metadata
            if copy and copy.status == PhysicalCopy.Status.ACTIVE:
                copy.status = PhysicalCopy.Status.RETIRED
                copy.save(update_fields=["status", "updated_at"])
            station = None

        item = shelf_book.marketplace_item
        if item:
            if item.is_deleted:
                item.restore()
            item.category = category
            item.book_title = shelf_book.book_title
            item.topic_id = data.get("topic_id")
            item.title = shelf_book.book_title.title
            item.description = description
            item.deal_type = deal_type
            item.delivery_type = delivery_type
            item.donation_methods = donation_methods
            item.physical_copy = linked_copy
            item.book_station = station
            item.shipping_payer = shipping_payer
            item.price = price
            item.discount_price = None
            item.stock = stock
            item.condition = item_condition
            item.city = city
            item.weight_grams = weight_grams
            item.digital_file_key = (data.get("digital_file_key") or item.digital_file_key or "").strip()
            item.file_format = (data.get("file_format") or item.file_format or "").strip()
            item.status = Item.Status.AVAILABLE
            item.save()
        else:
            item = Item.objects.create(
                seller=user,
                category=category,
                topic_id=data.get("topic_id"),
                book_title=shelf_book.book_title,
                title=shelf_book.book_title.title,
                description=description,
                deal_type=deal_type,
                delivery_type=delivery_type,
                donation_methods=donation_methods,
                physical_copy=linked_copy,
                book_station=station,
                shipping_payer=shipping_payer,
                price=price,
                stock=stock,
                condition=item_condition,
                city=city,
                weight_grams=weight_grams,
                digital_file_key=(data.get("digital_file_key") or "").strip(),
                file_format=(data.get("file_format") or "").strip(),
                status=Item.Status.AVAILABLE,
            )

        BookDetail.objects.update_or_create(
            item=item,
            defaults={
                "isbn": shelf_book.book_title.isbn,
                "author": shelf_book.book_title.author,
                "translator": shelf_book.book_title.translator or "",
                "publisher": shelf_book.book_title.publisher or "",
                "publication_year": shelf_book.book_title.publication_year,
            },
        )

        shelf_book.marketplace_item = item
        shelf_book.donation_methods = donation_methods
        shelf_book.preferred_station = station
        shelf_book.shipping_payer = shipping_payer
        shelf_book.disposition = (
            UserShelfBook.Disposition.FOR_SALE
            if deal_type == Item.DealType.SALE
            else UserShelfBook.Disposition.FOR_DONATION
        )
        shelf_book.save(
            update_fields=[
                "marketplace_item",
                "physical_copy",
                "donation_methods",
                "preferred_station",
                "shipping_payer",
                "disposition",
                "updated_at",
            ]
        )

        # Auto-inject synchronized book post into Topic chat if topic is set
        if item.topic and not item.post:
            from apps.notes.models import Post
            post_content = f"📖 **اهدای کتاب: {item.title}**\n\n{item.description or ''}"
            book_cover = None
            if shelf_book.book_title and shelf_book.book_title.cover_image:
                book_cover = shelf_book.book_title.cover_image.name

            post = Post.objects.create(
                topic=item.topic,
                author=user,
                content=post_content,
                media_type="image" if book_cover else "text",
                media_file=book_cover
            )
            item.post = post
            item.save(update_fields=['post'])
        elif item.topic and item.post:
            item.post.content = f"📖 **اهدای کتاب: {item.title}**\n\n{item.description or ''}"
            item.post.save(update_fields=['content', 'updated_at'])

        logger.info("Shelf book %s published to marketplace item=%s (%s, methods=%s)", shelf_book.id, item.id, deal_type, donation_methods)
        return shelf_book

    @classmethod
    @transaction.atomic
    def withdraw_offering(cls, user, shelf_book: UserShelfBook) -> UserShelfBook:
        """
        Returns a shelf book back to purely personal KEEPING status,
        archiving its active marketplace listing or retiring its held QR copy.
        """
        cls._assert_owner(user, shelf_book)
        cls._ensure_withdrawable_copy(user, shelf_book)

        cls._archive_active_offerings(shelf_book)
        shelf_book.disposition = UserShelfBook.Disposition.KEEPING
        shelf_book.donation_methods = []
        shelf_book.preferred_station = None
        shelf_book.save(update_fields=["disposition", "donation_methods", "preferred_station", "updated_at"])
        logger.info("Shelf book %s withdrawn back to KEEPING", shelf_book.id)
        return shelf_book

    @staticmethod
    def deduct_quantity_on_item_transfer(item: Item, qty: int) -> None:
        """
        Syncs owner's physical UserShelfBook quantity when an Item is transferred via DonationService or OrderService.
        """
        deducted = max(1, int(qty or 1))
        shelf_book = (
            UserShelfBook.all_objects.select_for_update()
            .filter(marketplace_item=item, deleted_at__isnull=True)
            .first()
        )
        if not shelf_book or shelf_book.book_format != UserShelfBook.BookFormat.PHYSICAL:
            return

        shelf_book.quantity = max(0, (shelf_book.quantity or 0) - deducted)
        update_fields = ["quantity", "updated_at"]

        if item.stock <= 0 or item.status == Item.Status.COMPLETED:
            copy = shelf_book.physical_copy
            if copy and copy.status == PhysicalCopy.Status.ACTIVE:
                copy.status = PhysicalCopy.Status.RETIRED
                copy.save(update_fields=["status", "updated_at"])
            shelf_book.physical_copy = None
            shelf_book.marketplace_item = None
            shelf_book.disposition = UserShelfBook.Disposition.KEEPING
            shelf_book.donation_methods = []
            shelf_book.preferred_station = None
            update_fields.extend([
                "physical_copy",
                "marketplace_item",
                "disposition",
                "donation_methods",
                "preferred_station",
            ])

        shelf_book.save(update_fields=update_fields)

    # ------------------------------------------------------------------
    # Book Donation to Phone & Handover Management (اهدای کتاب با شماره موبایل)
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def donate_to_phone(
        cls,
        user,
        shelf_book: UserShelfBook,
        quantity: int,
        recipient_phone: str,
        send_sms: bool = False,
    ) -> Dict[str, Any]:
        """
        Donates specified quantity of a shelf book to a recipient identified by phone number.
        - Checks available quantity (quantity - reserved_quantity) under lock.
        - Creates a Transfer record in PENDING_RECIPIENT.
        - Increments reserved_quantity on the shelf_book.
        - If send_sms is True: respects 2-minute cooldown and dispatches async SMS via Kavenegar.
        """
        cls._assert_owner(user, shelf_book)

        if shelf_book.is_gift:
            raise ShelfBookError("کتاب‌های هدیه‌گرفته‌شده در حال حاضر قابل اهدای مجدد نیستند.")

        locked_shelf_book = (
            UserShelfBook.objects.select_for_update()
            .get(id=shelf_book.id)
        )

        handover_qty = cls._validate_quantity(quantity, min_value=1)
        available_qty = locked_shelf_book.quantity - locked_shelf_book.reserved_quantity
        if handover_qty > available_qty:
            raise ShelfBookError(
                f"موجودی آزاد این کتاب {available_qty} جلد است؛ امکان اهدای {handover_qty} جلد وجود ندارد."
            )

        norm_phone = CirculationService._normalize_phone(recipient_phone)
        if not norm_phone or len(norm_phone) < 10:
            raise ShelfBookError("شماره موبایل گیرنده معتبر نیست.")

        donor_phone = CirculationService._normalize_phone(getattr(user, "phone", "") or getattr(user, "username", ""))
        if donor_phone and norm_phone == donor_phone:
            raise ShelfBookError("امکان اهدای کتاب به خودتان وجود ندارد.")

        recipient_user = User.objects.filter(phone=norm_phone).first()

        copy = locked_shelf_book.physical_copy
        if not copy:
            copy = CirculationService.register_physical_copy(
                user=user,
                book_title_id=locked_shelf_book.book_title_id,
                condition=locked_shelf_book.condition or PhysicalCopy.Condition.GOOD,
            )
            locked_shelf_book.physical_copy = copy
            locked_shelf_book.disposition = UserShelfBook.Disposition.CIRCULATING

        sms_sent = False
        if send_sms:
            two_mins_ago = timezone.now() - timedelta(minutes=2)
            recent_sms_transfer = Transfer.objects.filter(
                from_user=user,
                copy=copy,
                recipient_phone=norm_phone,
                created_at__gte=two_mins_ago,
            ).exists()
            if recent_sms_transfer:
                logger.info("SMS suppressed due to 2-minute cooldown for %s", norm_phone)
                sms_sent = False
            else:
                sms_sent = True

        transfer = Transfer.objects.create(
            copy=copy,
            from_user=user,
            to_user=recipient_user,
            recipient_phone=norm_phone,
            quantity=handover_qty,
            method=Transfer.Method.SCAN_CONFIRM,
            status=Transfer.Status.PENDING_RECIPIENT,
        )

        locked_shelf_book.reserved_quantity += handover_qty
        locked_shelf_book.save(update_fields=["reserved_quantity", "physical_copy", "disposition", "updated_at"])

        if sms_sent:
            cls._dispatch_async_donation_sms(
                phone=norm_phone,
                donor_name=user.get_full_name() or "همراه تفاخر",
                book_title=locked_shelf_book.book_title.title,
                quantity=handover_qty,
                short_code=copy.short_code,
            )

        return {
            "transfer_id": transfer.id,
            "short_code": copy.short_code,
            "book_title": locked_shelf_book.book_title.title,
            "quantity": handover_qty,
            "recipient_phone": norm_phone,
            "recipient_registered": bool(recipient_user),
            "recipient_name": recipient_user.get_full_name() if recipient_user else None,
            "sms_sent": sms_sent,
            "status": transfer.status,
        }

    @classmethod
    @transaction.atomic
    def confirm_gift(cls, user, transfer_id: int) -> Dict[str, Any]:
        """
        Recipient confirms receipt of a gifted book.
        - Decrements quantity and reserved_quantity from donor's shelf.
        - Adds gifted book to recipient's shelf with is_gift=True and gifted_by=donor.
        - Marks transfer confirmed.
        """
        if not user or not user.is_authenticated:
            raise ShelfBookError("برای تایید دریافت کتاب، ورود به حساب کاربری الزامی است.")

        user_phone = CirculationService._normalize_phone(getattr(user, "phone", "") or "")

        transfer = (
            Transfer.objects.select_for_update()
            .filter(id=transfer_id)
            .first()
        )
        if not transfer:
            raise ShelfBookError("اطلاعات این هدیه یافت نشد.")

        if transfer.status != Transfer.Status.PENDING_RECIPIENT:
            raise ShelfBookError("این انتقال قبلاً تعیین تکلیف شده یا لغو شده است.")

        is_matched_user = transfer.to_user_id == user.id
        is_matched_phone = bool(user_phone and transfer.recipient_phone == user_phone)
        if not (is_matched_user or is_matched_phone):
            raise ShelfBookError("شما گیرنده مجاز این کتاب نیستید.")

        donor = transfer.from_user
        gift_qty = transfer.quantity

        donor_shelf = (
            UserShelfBook.objects.select_for_update()
            .filter(user=donor, book_title=transfer.copy.book_title)
            .first()
        )
        if donor_shelf:
            donor_shelf.quantity = max(0, donor_shelf.quantity - gift_qty)
            donor_shelf.reserved_quantity = max(0, donor_shelf.reserved_quantity - gift_qty)
            donor_shelf.save(update_fields=["quantity", "reserved_quantity", "updated_at"])

        recipient_shelf, created = UserShelfBook.objects.select_for_update().get_or_create(
            user=user,
            book_title=transfer.copy.book_title,
            is_gift=True,
            defaults={
                "quantity": gift_qty,
                "gifted_by": donor,
                "book_format": UserShelfBook.BookFormat.PHYSICAL,
                "disposition": UserShelfBook.Disposition.KEEPING,
                "condition": transfer.copy.condition,
            },
        )
        if not created:
            recipient_shelf.quantity += gift_qty
            if not recipient_shelf.gifted_by and donor:
                recipient_shelf.gifted_by = donor
            recipient_shelf.is_gift = True
            recipient_shelf.save(update_fields=["quantity", "gifted_by", "is_gift", "updated_at"])

        transfer.to_user = user
        transfer.status = Transfer.Status.CONFIRMED
        transfer.confirmed_at = timezone.now()
        transfer.save(update_fields=["to_user", "status", "confirmed_at", "updated_at"])

        transfer.copy.current_holder = user
        transfer.copy.status = PhysicalCopy.Status.ACTIVE
        transfer.copy.transfer_count += 1
        transfer.copy.save(update_fields=["current_holder", "status", "transfer_count", "updated_at"])

        return {
            "transfer_id": transfer.id,
            "book_title": transfer.copy.book_title.title,
            "quantity": gift_qty,
            "status": "confirmed",
            "donor_name": donor.get_full_name() if donor else "همراه تفاخر",
        }

    @classmethod
    @transaction.atomic
    def reject_gift(cls, user, transfer_id: int) -> Dict[str, Any]:
        """
        Recipient rejects a gift. Returns reserved quantity to donor and marks transfer cancelled.
        """
        user_phone = CirculationService._normalize_phone(getattr(user, "phone", "") or "")
        transfer = (
            Transfer.objects.select_for_update()
            .filter(id=transfer_id)
            .first()
        )
        if not transfer:
            raise ShelfBookError("اطلاعات این هدیه یافت نشد.")
        if transfer.status != Transfer.Status.PENDING_RECIPIENT:
            raise ShelfBookError("این انتقال قبلاً تعیین تکلیف شده است.")

        is_matched_user = transfer.to_user_id == getattr(user, "id", None)
        is_matched_phone = bool(user_phone and transfer.recipient_phone == user_phone)
        if not (is_matched_user or is_matched_phone):
            raise ShelfBookError("شما گیرنده مجاز این کتاب نیستید.")

        if transfer.from_user:
            donor_shelf = (
                UserShelfBook.objects.select_for_update()
                .filter(user=transfer.from_user, book_title=transfer.copy.book_title)
                .first()
            )
            if donor_shelf:
                donor_shelf.reserved_quantity = max(0, donor_shelf.reserved_quantity - transfer.quantity)
                donor_shelf.save(update_fields=["reserved_quantity", "updated_at"])

        transfer.status = Transfer.Status.CANCELLED
        transfer.save(update_fields=["status", "updated_at"])
        return {"transfer_id": transfer.id, "status": "cancelled"}

    @classmethod
    @transaction.atomic
    def cancel_gift(cls, user, transfer_id: int) -> Dict[str, Any]:
        """
        Donor cancels a pending book gift before recipient confirms.
        """
        transfer = (
            Transfer.objects.select_for_update()
            .filter(id=transfer_id, from_user=user)
            .first()
        )
        if not transfer:
            raise ShelfBookError("هدیه‌ای با این مشخصات یافت نشد یا شما اجازه لغو آن را ندارید.")
        if transfer.status != Transfer.Status.PENDING_RECIPIENT:
            raise ShelfBookError("این هدیه قبلاً تایید یا لغو شده است.")

        donor_shelf = (
            UserShelfBook.objects.select_for_update()
            .filter(user=user, book_title=transfer.copy.book_title)
            .first()
        )
        if donor_shelf:
            donor_shelf.reserved_quantity = max(0, donor_shelf.reserved_quantity - transfer.quantity)
            donor_shelf.save(update_fields=["reserved_quantity", "updated_at"])

        transfer.status = Transfer.Status.CANCELLED
        transfer.save(update_fields=["status", "updated_at"])
        return {"transfer_id": transfer.id, "status": "cancelled"}

    @classmethod
    def get_incoming_gifts(cls, user) -> List[Dict[str, Any]]:
        """
        Returns all incoming pending gifts for the authenticated user (by user_id or phone).
        Zero N+1 query policy enforced with select_related.
        """
        if not user or not user.is_authenticated:
            return []
        phone = CirculationService._normalize_phone(getattr(user, "phone", "") or "")

        q_filter = Q(status=Transfer.Status.PENDING_RECIPIENT)
        if phone:
            q_filter &= (Q(to_user=user) | Q(recipient_phone=phone))
        else:
            q_filter &= Q(to_user=user)

        transfers = (
            Transfer.objects.filter(q_filter)
            .select_related("copy__book_title", "from_user")
            .order_by("-created_at")
        )

        results = []
        for trf in transfers:
            book_title = trf.copy.book_title
            cover_url = book_title.cover_image.url if book_title.cover_image else None
            results.append({
                "id": trf.id,
                "short_code": trf.copy.short_code,
                "book_title": {
                    "id": book_title.id,
                    "title": book_title.title,
                    "author": book_title.author,
                    "cover_image": cover_url,
                },
                "quantity": trf.quantity,
                "donor_name": trf.from_user.get_full_name() if trf.from_user else "همراه تفاخر",
                "created_at": trf.created_at.isoformat(),
            })
        return results

    @classmethod
    def _dispatch_async_donation_sms(
        cls,
        phone: str,
        donor_name: str,
        book_title: str,
        quantity: int,
        short_code: str,
    ) -> None:
        """
        Sends book donation SMS asynchronously in a background daemon thread
        so it never blocks the HTTP web request cycle.
        """
        import threading
        from django.conf import settings

        def _send():
            try:
                from apps.accounts.services import kavenegar_configured
                if not kavenegar_configured():
                    logger.info("[MOCK SMS] Book donation SMS to %s: %s donated '%s'", phone, donor_name, book_title)
                    return

                from kavenegar import KavenegarAPI
                api = KavenegarAPI(settings.KAVENEGAR_API_KEY.strip())
                frontend_url = getattr(settings, "FRONTEND_BASE_URL", "https://tafakormag.ir").rstrip("/")
                book_link = f"{frontend_url}/b/{short_code}"
                qty_text = f"{quantity} جلد " if quantity > 1 else ""
                message = f"سلام، {qty_text}کتاب «{book_title}» از طرف {donor_name} به شما در تفاخر اهدا شد.\nمشاهده و دریافت: {book_link}"

                params = {
                    "sender": settings.KAVENEGAR_SENDER.strip(),
                    "receptor": phone,
                    "message": message,
                }
                api.sms_send(params)
                logger.info("Donation SMS dispatched successfully to %s for book %s", phone, short_code)
            except Exception as e:
                logger.exception("Failed to send donation SMS to %s: %s", phone, e)

        thread = threading.Thread(target=_send, daemon=True)
        thread.start()

