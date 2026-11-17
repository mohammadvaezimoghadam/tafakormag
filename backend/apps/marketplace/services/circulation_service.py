import logging
import hashlib
import secrets
from datetime import timedelta
from typing import Optional, Dict, Any, List, Tuple
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.notes.models import normalize_persian_text
from ..utils import format_user_display_name
from ..models.circulation import (
    BookTitle,
    BookStation,
    PhysicalCopy,
    Transfer,
    Badge,
)
from ..exceptions import (
    CirculationError,
    BookCopyNotFoundError,
    UnauthorizedBookActionError,
    BookNotAvailableForHandoverError,
    SelfHandoverError,
    TransferCooldownActiveError,
    DailyTransferLimitExceededError,
    InvalidOtpError,
    StationFullError,
    BookNotInStationError,
)
from .badge_service import BadgeService

logger = logging.getLogger(__name__)
User = get_user_model()


class CirculationService:
    """
    Core Domain Service orchestrating physical book circulation (شبکه گردش و اهدای کتاب).
    Enforces all ADR anti-fraud guardrails, 2-step confirmations, station deposits, and badges.
    Strictly follows the Tafakor Service Layer pattern (thin views, fat services).
    """

    OTP_EXPIRY_MINUTES = 15
    COOLDOWN_HOURS = 72
    DAILY_DONATION_LIMIT = 2

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def clean_short_code(raw_code: str) -> str:
        """
        Cleans and extracts canonical short code from raw inputs or scanned URLs.
        e.g., 'https://tafakormag.ir/b/TK-8492' -> 'TK-8492'
        """
        if not raw_code:
            return ""
        code = str(raw_code).strip()
        if "?" in code:
            code = code.split("?")[0]
        if "/" in code:
            code = code.rstrip("/").split("/")[-1]
        return code.strip().upper()

    @staticmethod
    def _hash_otp(otp_code: str, salt: str) -> str:
        return hashlib.sha256(f"{otp_code}:{salt}".encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_4digit_otp() -> str:
        return "".join(secrets.choice("0123456789") for _ in range(4))

    @staticmethod
    def _normalize_phone(raw_phone: str) -> str:
        """Converts Persian/Arabic numerals and +98 prefixes to canonical 09XXXXXXXXX."""
        if not raw_phone:
            return ""
        digits_map = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        cleaned = str(raw_phone).translate(digits_map)
        cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch == "+")
        if cleaned.startswith("+98"):
            cleaned = "0" + cleaned[3:]
        elif cleaned.startswith("0098"):
            cleaned = "0" + cleaned[4:]
        elif cleaned.startswith("98") and len(cleaned) == 12:
            cleaned = "0" + cleaned[2:]
        elif len(cleaned) == 10 and cleaned.startswith("9"):
            cleaned = "0" + cleaned
        return cleaned.strip()

    # ------------------------------------------------------------------
    # 1. Catalog & Physical Copy Registration
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def register_book_title(cls, user, data: Dict[str, Any]) -> BookTitle:
        """
        Registers or retrieves a master BookTitle entity with canonical Persian normalization.
        """
        title = data.get("title", "").strip()
        author = data.get("author", "").strip()
        isbn = data.get("isbn") or None

        norm_title = normalize_persian_text(title)
        norm_author = normalize_persian_text(author)

        # 1. Lookup by ISBN if provided
        if isbn:
            existing = BookTitle.objects.filter(isbn=isbn).first()
            if existing:
                return existing

        # 2. Lookup by normalized title and author
        existing = BookTitle.objects.filter(
            normalized_title=norm_title,
            normalized_author=norm_author
        ).first()
        if existing:
            return existing

        # 3. Create new master title
        source = BookTitle.Source.ADMIN if (user and (user.is_staff or user.is_superuser)) else BookTitle.Source.MANUAL
        book_title = BookTitle.objects.create(
            title=title,
            author=author,
            translator=data.get("translator", ""),
            publisher=data.get("publisher", ""),
            category=data.get("category", ""),
            isbn=isbn,
            publication_year=data.get("publication_year"),
            edition=data.get("edition", ""),
            description=data.get("description", ""),
            cover_image=data.get("cover_image"),
            source=source,
            verified_by_admin=bool(user and user.is_staff)
        )
        logger.info("Created new BookTitle '%s' by user %s", book_title.title, getattr(user, 'id', None))
        return book_title

    @classmethod
    @transaction.atomic
    def register_physical_copy(
        cls,
        user,
        book_title_id: Optional[int] = None,
        title: str = "",
        author: str = "",
        publisher: str = "",
        quantity: int = 1,
        cover_image: Any = None,
        condition: str = PhysicalCopy.Condition.GOOD,
        privacy: str = PhysicalCopy.Privacy.FIRST_NAME_ONLY
    ) -> PhysicalCopy:
        """
        Registers a new physical book copy into the circulation platform.
        Generates a collision-resistant short_code and assigns initial holder.
        """
        if not user or not user.is_authenticated:
            raise UnauthorizedBookActionError("برای ثبت کتاب فیزیکی ورود به حساب کاربری الزامی است.")

        if book_title_id:
            try:
                book_title = BookTitle.objects.get(id=book_title_id)
            except BookTitle.DoesNotExist:
                raise BookCopyNotFoundError("عنوان مرجع کتاب یافت نشد.")
        else:
            title_clean = (title or "").strip()
            author_clean = (author or "").strip()
            if not title_clean:
                raise UnauthorizedBookActionError("عنوان کتاب الزامی است.")
            book_title, _ = BookTitle.objects.get_or_create(
                title=title_clean,
                defaults={
                    "author": author_clean,
                    "publisher": (publisher or "").strip(),
                }
            )

        if cover_image:
            book_title.cover_image = cover_image
            book_title.save(update_fields=["cover_image", "updated_at"])

        short_code = PhysicalCopy.generate_unique_short_code()
        copy = PhysicalCopy.objects.create(
            short_code=short_code,
            book_title=book_title,
            current_holder=user,
            registered_by=user,
            original_donor=user,
            status=PhysicalCopy.Status.ACTIVE,
            condition=condition,
            privacy=privacy
        )

        from ..models.shelf import UserShelfBook
        qty = max(1, int(quantity))
        shelf_book, created = UserShelfBook.objects.get_or_create(
            user=user,
            book_title=book_title,
            defaults={
                "quantity": qty,
                "disposition": UserShelfBook.Disposition.FOR_DONATION,
                "book_format": UserShelfBook.BookFormat.PHYSICAL,
                "condition": condition,
                "physical_copy": copy,
            }
        )
        if not created and shelf_book.quantity < qty:
            shelf_book.quantity = qty
            shelf_book.save(update_fields=["quantity", "updated_at"])
        if not shelf_book.physical_copy:
            shelf_book.physical_copy = copy
            shelf_book.save(update_fields=["physical_copy", "updated_at"])

        logger.info("PhysicalCopy %s registered for book '%s' by user %s", short_code, book_title.title, user.id)
        return copy

    # ------------------------------------------------------------------
    # 2. Copy Inspection (Scan & Context Lookup)
    # ------------------------------------------------------------------
    @classmethod
    def inspect_copy_by_code(cls, user, raw_short_code: str) -> Dict[str, Any]:
        """
        High-performance copy lookup optimized with select_related and prefetch_related.
        Determines user-specific actions (can_claim, is_holder, active_transfer, etc.).
        """
        short_code = cls.clean_short_code(raw_short_code)
        try:
            copy = PhysicalCopy.objects.select_related(
                "book_title",
                "current_holder",
                "registered_by",
                "original_donor",
                "station__city"
            ).prefetch_related(
                "transfers__from_user",
                "transfers__to_user",
                "transfers__station"
            ).get(short_code=short_code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError(f"نسخه فیزیکی با شناسه {short_code} در سیستم یافت نشد.")

        is_authenticated = bool(user and user.is_authenticated)
        user_id = user.id if is_authenticated else None
        is_holder = (is_authenticated and copy.current_holder_id == user_id)

        # Check pending transfer
        active_transfer = None
        if copy.status == PhysicalCopy.Status.TRANSFERRING:
            active_transfer = copy.transfers.filter(
                status__in=[Transfer.Status.PENDING_DONOR, Transfer.Status.PENDING_RECIPIENT]
            ).first()

        can_claim = False
        if is_authenticated and not is_holder:
            if copy.status == PhysicalCopy.Status.ACTIVE:
                can_claim = True
            elif copy.status == PhysicalCopy.Status.IN_STATION:
                can_claim = True
            elif copy.status == PhysicalCopy.Status.TRANSFERRING and active_transfer:
                if active_transfer.to_user_id == user_id or active_transfer.to_user_id is None:
                    can_claim = True

        return {
            "copy": copy,
            "book_title": copy.book_title,
            "is_holder": is_holder,
            "can_claim": can_claim,
            "active_transfer": active_transfer,
            "current_station": copy.station,
            "total_transfers": copy.transfer_count,
            "available_quantity": cls._get_copy_max_handover_quantity(copy),
        }

    # ------------------------------------------------------------------
    # 3. In-Person Handover Workflows (Scan & Confirm, OTP Fallback)
    # ------------------------------------------------------------------
    @classmethod
    def _get_copy_max_handover_quantity(cls, copy: PhysicalCopy) -> int:
        from ..models.catalog import Item
        from ..models.shelf import UserShelfBook

        owner_shelf = UserShelfBook.objects.filter(physical_copy=copy).first()
        linked_item = Item.objects.filter(
            physical_copy=copy,
            deal_type=Item.DealType.DONATION,
            status=Item.Status.AVAILABLE,
        ).first()

        shelf_qty = owner_shelf.quantity if (owner_shelf and owner_shelf.quantity > 0) else 1
        if linked_item and linked_item.stock > 0:
            if owner_shelf and owner_shelf.quantity > 0:
                return max(1, min(linked_item.stock, owner_shelf.quantity))
            return max(1, linked_item.stock)
        return max(1, shelf_qty)

    @classmethod
    @transaction.atomic
    def initiate_handover(
        cls,
        donor_user,
        short_code: str,
        recipient_user=None,
        recipient_phone: Optional[str] = None,
        method: str = Transfer.Method.SCAN_CONFIRM,
        donor_note: str = "",
        quantity: int = 1,
    ) -> Tuple[Transfer, Optional[str]]:
        """
        Donor initiates handover to a recipient.
        Enforces ADR-009 anti-fraud: 72h cooldown & 2/day daily limit.
        """
        code = cls.clean_short_code(short_code)
        try:
            copy = PhysicalCopy.objects.select_for_update().get(short_code=code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError("نسخه فیزیکی کتاب یافت نشد.")

        # Guard: Donor must be current holder
        if copy.current_holder_id != donor_user.id:
            raise UnauthorizedBookActionError()

        # Re-entrant handling: allow donor to refresh/update an open PENDING_RECIPIENT session,
        # while blocking if a recipient claim is already waiting for donor confirmation.
        if copy.status == PhysicalCopy.Status.TRANSFERRING:
            active_transfers = list(
                Transfer.objects.select_for_update().filter(
                    copy=copy,
                    status__in=[Transfer.Status.PENDING_DONOR, Transfer.Status.PENDING_RECIPIENT],
                )
            )
            if any(trf.status == Transfer.Status.PENDING_DONOR for trf in active_transfers):
                raise CirculationError(
                    "درخواست دریافت حضوری این کتاب هم‌اکنون در انتظار تایید نهایی شماست."
                )
            for stale in active_transfers:
                stale.status = Transfer.Status.CANCELLED
                stale.save(update_fields=["status", "updated_at"])
            copy.status = PhysicalCopy.Status.ACTIVE
            copy.save(update_fields=["status", "updated_at"])

        # Guard: Copy must be currently active
        if copy.status != PhysicalCopy.Status.ACTIVE:
            raise BookNotAvailableForHandoverError()

        handover_qty = int(quantity or 1)
        if handover_qty < 1:
            raise CirculationError("تعداد کتاب برای تحویل باید حداقل ۱ جلد باشد.")
        max_qty = cls._get_copy_max_handover_quantity(copy)
        if handover_qty > max_qty:
            raise CirculationError(f"حداکثر {max_qty} جلد از این کتاب برای تحویل در دسترس است.")

        # Resolve recipient if phone is provided (mandatory Tafakor registration)
        if not recipient_user and recipient_phone:
            norm_phone = cls._normalize_phone(recipient_phone)
            if norm_phone:
                recipient_user = User.objects.filter(phone=norm_phone).first()
                if not recipient_user:
                    raise CirculationError(
                        "کاربری با این شماره موبایل در تفاخر ثبت‌نام نکرده است. گیرنده باید ابتدا وارد تفاخر شود یا از QR / کد تحویل استفاده کنید."
                    )

        # If recipient is identified upfront:
        plain_otp = None
        otp_hash = ""
        otp_expires_at = None

        if recipient_user:
            if recipient_user.id == donor_user.id:
                raise SelfHandoverError()

            # Anti-fraud 1: 72-hour cooldown check
            cls._verify_cooldown(copy, recipient_user)

        # Anti-fraud 2: Daily donation cap for donor
        cls._verify_daily_limit(donor_user)

        # If method is OTP fallback, generate 4-digit code
        if method == Transfer.Method.OTP_FALLBACK:
            plain_otp = cls._generate_4digit_otp()
            otp_hash = cls._hash_otp(plain_otp, str(copy.id))
            otp_expires_at = timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)

        # Update copy status to transferring
        copy.status = PhysicalCopy.Status.TRANSFERRING
        copy.save(update_fields=["status", "updated_at"])

        # Determine pending status:
        # If donor specifies recipient, wait for recipient to confirm (PENDING_RECIPIENT)
        # If open handover (waiting for scan), PENDING_RECIPIENT
        transfer_status = Transfer.Status.PENDING_RECIPIENT

        transfer = Transfer.objects.create(
            copy=copy,
            from_user=donor_user,
            to_user=recipient_user,
            method=method,
            status=transfer_status,
            quantity=handover_qty,
            otp_code_hash=otp_hash,
            otp_expires_at=otp_expires_at,
            donor_note=donor_note.strip()
        )

        if recipient_user:
            donor_name = cls._format_user_privacy(donor_user, copy.privacy)
            cls._enqueue_bot_notification(
                recipient_user,
                (
                    f"📚 همراه گرامی تفاخر،\n"
                    f"«{donor_name}» کتاب «{copy.book_title.title}» [{code}] ({handover_qty} جلد) را برای تحویل حضوری به شما ثبت کرد.\n"
                    f"لطفاً در بخش «تحویل گرفتم» تفاخر دریافت آن را تایید کنید."
                ),
            )

        logger.info(
            "Handover initiated for copy %s by donor %s (method: %s, transfer: %s)",
            code, donor_user.id, method, transfer.id
        )
        return transfer, plain_otp

    @classmethod
    @transaction.atomic
    def claim_by_recipient(
        cls,
        recipient_user,
        short_code: str,
        recipient_note: str = "",
        quantity: int = 1,
    ) -> Transfer:
        """
        Recipient scans the book's QR code in person to request / initiate claim.
        Enforces 72h cooldown and transitions to PENDING_DONOR for donor's 1-tap confirmation.
        """
        code = cls.clean_short_code(short_code)
        try:
            copy = PhysicalCopy.objects.select_for_update(of=("self",)).select_related("current_holder").get(short_code=code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError("نسخه فیزیکی کتاب یافت نشد.")

        if copy.current_holder_id == recipient_user.id:
            raise SelfHandoverError("شما در حال حاضر دارنده این کتاب هستید.")

        # Guard: Check 72h cooldown
        cls._verify_cooldown(copy, recipient_user)

        handover_qty = int(quantity or 1)
        if handover_qty < 1:
            raise CirculationError("تعداد کتاب درخواستی باید حداقل ۱ جلد باشد.")
        max_qty = cls._get_copy_max_handover_quantity(copy)
        if handover_qty > max_qty:
            raise CirculationError(f"حداکثر {max_qty} جلد از این کتاب برای تحویل در دسترس است.")

        # Check existing active transfer
        existing_transfer = Transfer.objects.select_for_update().filter(
            copy=copy,
            status__in=[Transfer.Status.PENDING_DONOR, Transfer.Status.PENDING_RECIPIENT]
        ).first()

        if existing_transfer:
            # If transfer was waiting for recipient (even if an open OTP was shown alongside QR),
            # convert it cleanly to donor-tap confirmation so both QR claim and OTP stay compatible.
            if existing_transfer.to_user is None or existing_transfer.to_user_id == recipient_user.id:
                existing_transfer.to_user = recipient_user
                existing_transfer.method = Transfer.Method.SCAN_CONFIRM
                existing_transfer.otp_code_hash = ""
                existing_transfer.otp_expires_at = None
                existing_transfer.quantity = handover_qty
                if recipient_note:
                    existing_transfer.recipient_note = recipient_note.strip()
                existing_transfer.status = Transfer.Status.PENDING_DONOR
                existing_transfer.save(
                    update_fields=[
                        "to_user",
                        "method",
                        "otp_code_hash",
                        "otp_expires_at",
                        "quantity",
                        "recipient_note",
                        "status",
                        "updated_at",
                    ]
                )
                if copy.current_holder:
                    recipient_name = cls._format_user_privacy(recipient_user, copy.privacy)
                    cls._enqueue_bot_notification(
                        copy.current_holder,
                        (
                            f"📚 همراه گرامی تفاخر،\n"
                            f"«{recipient_name}» درخواست دریافت حضوری کتاب «{copy.book_title.title}» [{code}] را ثبت کرد.\n"
                            f"لطفاً در تفاخر انتقال را تایید فرمایید."
                        ),
                    )
                return existing_transfer
            else:
                raise BookNotAvailableForHandoverError("این کتاب در حال حاضر در انتظار واگذاری به شخص دیگری است.")

        if copy.status not in [PhysicalCopy.Status.ACTIVE, PhysicalCopy.Status.TRANSFERRING]:
            raise BookNotAvailableForHandoverError()

        # Create new transfer pending donor confirmation
        copy.status = PhysicalCopy.Status.TRANSFERRING
        copy.save(update_fields=["status", "updated_at"])

        transfer = Transfer.objects.create(
            copy=copy,
            from_user=copy.current_holder,
            to_user=recipient_user,
            method=Transfer.Method.SCAN_CONFIRM,
            status=Transfer.Status.PENDING_DONOR,
            quantity=handover_qty,
            recipient_note=recipient_note.strip()
        )

        # Asynchronous bot notification to donor if Telegram/Bale is connected (skill: bot-task-queue)
        if copy.current_holder:
            recipient_name = cls._format_user_privacy(recipient_user, copy.privacy)
            msg = (
                f"📚 همراه گرامی تفاخر،\n"
                f"«{recipient_name}» درخواست دریافت حضوری کتاب «{copy.book_title.title}» [{code}] را ثبت کرد.\n"
                f"لطفاً در تفاخر شاپ با یک تپ انتقال را تایید فرمایید."
            )
            cls._enqueue_bot_notification(copy.current_holder, msg)

        logger.info(
            "Claim initiated by recipient %s for copy %s from holder %s",
            recipient_user.id, code, getattr(copy.current_holder, 'id', None)
        )
        return transfer

    @classmethod
    @transaction.atomic
    def confirm_handover(
        cls,
        user,
        transfer_id: int,
        otp_code: Optional[str] = None,
        donor_note: str = "",
        recipient_note: str = "",
        quantity: Optional[int] = None,
    ) -> Transfer:
        """
        Finalizes an in-person handover atomically:
        - Reassigns copy.current_holder to to_user
        - Increments copy.transfer_count
        - Sets copy.status = ACTIVE
        - Sets transfer.status = CONFIRMED, confirmed_at = now
        - Triggers Badge evaluation for both parties
        """
        try:
            transfer = Transfer.objects.select_for_update(of=("self",)).select_related("copy", "from_user", "to_user").get(id=transfer_id)
        except Transfer.DoesNotExist:
            raise CirculationError("شناسه انتقال یافت نشد.")

        if transfer.status != Transfer.Status.PENDING_DONOR and transfer.status != Transfer.Status.PENDING_RECIPIENT:
            raise CirculationError("این انتقال قبلاً تعیین وضعیت شده یا منقضی شده است.")

        copy = transfer.copy
        PhysicalCopy.objects.select_for_update().filter(id=copy.id).exists()

        # Authorization check:
        # Case 1: OTP Fallback verification
        if transfer.method == Transfer.Method.OTP_FALLBACK:
            if not otp_code:
                raise InvalidOtpError("کد تایید ۴ رقمی ارسال نشده است.")
            if transfer.otp_expires_at and timezone.now() > transfer.otp_expires_at:
                transfer.status = Transfer.Status.EXPIRED
                transfer.save(update_fields=["status", "updated_at"])
                copy.status = PhysicalCopy.Status.ACTIVE
                copy.save(update_fields=["status", "updated_at"])
                raise InvalidOtpError("مهلت زمانی کد تایید موقت منقضی شده است.")

            expected_hash = cls._hash_otp(str(otp_code).strip(), str(copy.id))
            if expected_hash != transfer.otp_code_hash:
                raise InvalidOtpError("کد تایید وارد شده نادرست است.")

            # With OTP, to_user can be bound here if user is confirming
            if transfer.to_user is None and user and user.is_authenticated:
                transfer.to_user = user

        # Case 2: Scan & Confirm verification
        elif transfer.status == Transfer.Status.PENDING_DONOR:
            # Donor confirms recipient's claim
            if user.id != transfer.from_user_id:
                raise UnauthorizedBookActionError("فقط اهداکننده می‌تواند انتقال را نهایی و تایید کند.")
        elif transfer.status == Transfer.Status.PENDING_RECIPIENT:
            # Recipient confirms
            if transfer.to_user and user.id != transfer.to_user_id:
                raise UnauthorizedBookActionError("فقط گیرنده مشخص شده می‌تواند انتقال را تایید کند.")
            if not transfer.to_user:
                transfer.to_user = user

        if not transfer.to_user:
            raise CirculationError("گیرنده نهایی کتاب مشخص نشده است.")

        if donor_note and user and transfer.from_user_id == user.id:
            transfer.donor_note = donor_note.strip()
        if recipient_note:
            transfer.recipient_note = recipient_note.strip()

        max_qty = cls._get_copy_max_handover_quantity(copy)
        if quantity is not None:
            handover_qty = int(quantity)
            if handover_qty < 1:
                raise CirculationError("تعداد کتاب تحویلی باید حداقل ۱ جلد باشد.")
            if handover_qty > max_qty:
                raise CirculationError(f"حداکثر {max_qty} جلد از این کتاب برای تحویل در دسترس است.")
        else:
            handover_qty = min(max(1, int(transfer.quantity or 1)), max_qty)

        now = timezone.now()
        transfer.quantity = handover_qty
        transfer.status = Transfer.Status.CONFIRMED
        transfer.confirmed_at = now
        transfer.save()

        # Update PhysicalCopy holder and status
        copy.current_holder = transfer.to_user
        copy.status = PhysicalCopy.Status.ACTIVE
        copy.station = None
        copy.transfer_count += 1
        copy.save(update_fields=["current_holder", "status", "station", "transfer_count", "updated_at"])
        cls._finalize_handover_inventory(
            copy=copy,
            recipient_user=transfer.to_user,
            handover_qty=handover_qty,
            acquired_label=f"اهدا حضوری ({copy.short_code})",
            gifted_by=transfer.from_user,
        )

        # Trigger gamification badge evaluation
        if transfer.from_user:
            BadgeService.evaluate_user_badges(transfer.from_user)
        if transfer.to_user:
            BadgeService.evaluate_user_badges(transfer.to_user)

        # Notify recipient via BotTask (skill: bot-task-queue)
        if transfer.to_user:
            confirm_msg = (
                f"🎉 انتقال کتاب «{copy.book_title.title}» [{copy.short_code}] تایید شد!\n"
                f"این کتاب اکنون در لیست کتاب‌های همراه شما در تفاخر شاپ ثبت گردید. با آرزوی مطالعه‌ای پربار."
            )
            cls._enqueue_bot_notification(transfer.to_user, confirm_msg)

        logger.info(
            "Transfer %s confirmed: copy %s passed from user %s to user %s",
            transfer.id, copy.short_code, getattr(transfer.from_user, 'id', None), transfer.to_user_id
        )
        return transfer

    @classmethod
    @transaction.atomic
    def cancel_handover(cls, user, transfer_id: int) -> Transfer:
        """
        Cancels a pending handover and restores the copy to ACTIVE state.
        Allowed by either party.
        """
        try:
            transfer = Transfer.objects.select_for_update().select_related("copy").get(id=transfer_id)
        except Transfer.DoesNotExist:
            raise CirculationError("شناسه انتقال یافت نشد.")

        if transfer.status not in [Transfer.Status.PENDING_DONOR, Transfer.Status.PENDING_RECIPIENT]:
            raise CirculationError("امکان لغو انتقال‌های قطعی یا منقضی شده وجود ندارد.")

        if user.id != transfer.from_user_id and user.id != getattr(transfer.to_user, 'id', None):
            raise UnauthorizedBookActionError("شما دسترسی لازم برای لغو این انتقال را ندارید.")

        transfer.status = Transfer.Status.CANCELLED
        transfer.save(update_fields=["status", "updated_at"])

        copy = transfer.copy
        copy.status = PhysicalCopy.Status.ACTIVE
        copy.save(update_fields=["status", "updated_at"])

        logger.info("Transfer %s cancelled by user %s", transfer.id, user.id)
        return transfer

    @classmethod
    def list_incoming_handovers(cls, user) -> List[Transfer]:
        """
        Lists active in-person transfers addressed directly to `user` (e.g. via recipient_phone)
        so recipients can confirm receipt in 1 tap without typing any codes.
        """
        if not user or not user.is_authenticated:
            return []
        now = timezone.now()
        return list(
            Transfer.objects.filter(
                to_user=user,
                status__in=[Transfer.Status.PENDING_RECIPIENT, Transfer.Status.PENDING_DONOR],
                copy__status=PhysicalCopy.Status.TRANSFERRING,
            )
            .filter(Q(otp_expires_at__isnull=True) | Q(otp_expires_at__gte=now))
            .select_related("copy__book_title", "from_user", "to_user", "station")
            .order_by("-created_at")
        )

    # ------------------------------------------------------------------
    # 4. Public Kiosk / Station Operations (ADR-005)
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def deposit_to_station(
        cls,
        user,
        short_code: str,
        station_id: int,
        donor_note: str = ""
    ) -> Tuple[PhysicalCopy, Transfer]:
        """
        User deposits a physical book into a public Tafakor kiosk/shelf.
        Capacity is checked and transfer logged as STATION_DEPOSIT.
        """
        code = cls.clean_short_code(short_code)
        try:
            copy = PhysicalCopy.objects.select_for_update().get(short_code=code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError("نسخه فیزیکی کتاب یافت نشد.")

        if copy.current_holder_id != user.id:
            raise UnauthorizedBookActionError()

        if copy.status != PhysicalCopy.Status.ACTIVE:
            raise BookNotAvailableForHandoverError()

        try:
            station = BookStation.objects.get(id=station_id, is_active=True)
        except BookStation.DoesNotExist:
            raise CirculationError("ایستگاه یا قفسه تفاخر انتخاب‌شده فعال نیست یا یافت نشد.")

        # Capacity check
        current_station_books = PhysicalCopy.objects.filter(
            station=station,
            status=PhysicalCopy.Status.IN_STATION
        ).count()

        if current_station_books >= station.capacity:
            raise StationFullError()

        now = timezone.now()
        copy.current_holder = None
        copy.station = station
        copy.status = PhysicalCopy.Status.IN_STATION
        copy.transfer_count += 1
        copy.save(update_fields=["current_holder", "station", "status", "transfer_count", "updated_at"])

        transfer = Transfer.objects.create(
            copy=copy,
            from_user=user,
            to_user=None,
            station=station,
            method=Transfer.Method.STATION_DEPOSIT,
            status=Transfer.Status.CONFIRMED,
            donor_note=donor_note.strip(),
            confirmed_at=now
        )

        BadgeService.evaluate_user_badges(user)
        logger.info("Copy %s deposited into station %s by user %s", code, station.id, user.id)
        return copy, transfer

    @classmethod
    @transaction.atomic
    def pickup_from_station(
        cls,
        user,
        short_code: str,
        recipient_note: str = ""
    ) -> Tuple[PhysicalCopy, Transfer]:
        """
        User scans and picks up a book directly from a physical kiosk/shelf.
        Enforces 72h anti-churn cooldown and reassigns holder to user.
        """
        code = cls.clean_short_code(short_code)
        try:
            copy = PhysicalCopy.objects.select_for_update(of=("self",)).select_related("station").get(short_code=code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError("نسخه فیزیکی کتاب یافت نشد.")

        if copy.status != PhysicalCopy.Status.IN_STATION or not copy.station:
            raise BookNotInStationError()

        # Cooldown: cannot pick up immediately if user just deposited it
        cls._verify_cooldown(copy, user)

        origin_station = copy.station
        now = timezone.now()

        copy.current_holder = user
        copy.station = None
        copy.status = PhysicalCopy.Status.ACTIVE
        copy.transfer_count += 1
        copy.save(update_fields=["current_holder", "station", "status", "transfer_count", "updated_at"])
        cls._finalize_handover_inventory(
            copy=copy,
            recipient_user=user,
            handover_qty=1,
            acquired_label=f"ایستگاه تفاخر ({origin_station.name})",
            gifted_by=copy.original_donor,
        )

        transfer = Transfer.objects.create(
            copy=copy,
            from_user=None,
            to_user=user,
            station=origin_station,
            method=Transfer.Method.STATION_PICKUP,
            status=Transfer.Status.CONFIRMED,
            recipient_note=recipient_note.strip(),
            confirmed_at=now
        )

        BadgeService.evaluate_user_badges(user)
        logger.info("Copy %s picked up from station %s by user %s", code, origin_station.id, user.id)
        return copy, transfer

    # ------------------------------------------------------------------
    # 5. Journey & Timeline (Optimized & Privacy-Preserving)
    # ------------------------------------------------------------------
    @classmethod
    def get_copy_journey(cls, raw_short_code: str) -> Dict[str, Any]:
        """
        Fetches the complete movement history of a copy with N+1 prevention
        and privacy-preserving holder names.
        """
        code = cls.clean_short_code(raw_short_code)
        try:
            copy = PhysicalCopy.objects.select_related(
                "book_title",
                "original_donor",
                "current_holder",
                "station__city"
            ).get(short_code=code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError("نسخه فیزیکی کتاب یافت نشد.")

        transfers = Transfer.objects.filter(
            copy=copy,
            status=Transfer.Status.CONFIRMED
        ).select_related(
            "from_user",
            "to_user",
            "station__city"
        ).order_by("confirmed_at")

        journey_events = []
        for trf in transfers:
            journey_events.append({
                "id": trf.id,
                "method": trf.method,
                "method_display": trf.get_method_display(),
                "quantity": trf.quantity,
                "from_display_name": cls._format_user_privacy(trf.from_user, copy.privacy),
                "to_display_name": cls._format_user_privacy(trf.to_user, copy.privacy),
                "station_name": trf.station.name if trf.station else None,
                "city_name": trf.station.city.name if (trf.station and trf.station.city) else None,
                "donor_note": trf.donor_note,
                "recipient_note": trf.recipient_note,
                "date": trf.confirmed_at or trf.created_at,
            })

        return {
            "copy": copy,
            "book_title": copy.book_title,
            "total_transfers": copy.transfer_count,
            "journey": journey_events
        }

    # ------------------------------------------------------------------
    # 6. Lifecycle Management: Lost / Retire
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def report_lost(cls, user, short_code: str, reason: str = "") -> PhysicalCopy:
        code = cls.clean_short_code(short_code)
        try:
            copy = PhysicalCopy.objects.select_for_update().get(short_code=code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError()

        if copy.current_holder_id != user.id:
            raise UnauthorizedBookActionError()

        copy.status = PhysicalCopy.Status.LOST
        copy.save(update_fields=["status", "updated_at"])
        logger.warning("Copy %s reported LOST by user %s (reason: %s)", code, user.id, reason)
        return copy

    @classmethod
    @transaction.atomic
    def retire_copy(cls, user, short_code: str, reason: str = "") -> PhysicalCopy:
        code = cls.clean_short_code(short_code)
        try:
            copy = PhysicalCopy.objects.select_for_update().get(short_code=code)
        except PhysicalCopy.DoesNotExist:
            raise BookCopyNotFoundError()

        if copy.current_holder_id != user.id:
            raise UnauthorizedBookActionError()

        copy.status = PhysicalCopy.Status.RETIRED
        copy.save(update_fields=["status", "updated_at"])
        logger.info("Copy %s retired by user %s (reason: %s)", code, user.id, reason)
        return copy

    # ------------------------------------------------------------------
    # Internal Anti-Fraud Checks
    # ------------------------------------------------------------------
    @classmethod
    def _verify_cooldown(cls, copy: PhysicalCopy, user) -> None:
        """
        Anti-fraud rule: 72h cooldown before book can return to previous holder (ADR-009).
        """
        cutoff = timezone.now() - timedelta(hours=cls.COOLDOWN_HOURS)
        recent_held = Transfer.objects.filter(
            copy=copy,
            from_user=user,
            status=Transfer.Status.CONFIRMED,
            confirmed_at__gte=cutoff
        ).exists()

        if recent_held:
            raise TransferCooldownActiveError()

    @classmethod
    def _verify_daily_limit(cls, user) -> None:
        """
        Anti-fraud rule: Max 2 handovers/day per user (ADR-009).
        """
        cutoff = timezone.now() - timedelta(days=1)
        recent_count = Transfer.objects.filter(
            from_user=user,
            status=Transfer.Status.CONFIRMED,
            confirmed_at__gte=cutoff
        ).count()

        if recent_count >= cls.DAILY_DONATION_LIMIT:
            raise DailyTransferLimitExceededError()

    @staticmethod
    def _format_user_privacy(user, privacy_mode: str) -> str:
        if not user:
            return "قفسه تفاخر"

        if privacy_mode == PhysicalCopy.Privacy.ANONYMOUS:
            return "یک همراه ناشناس تفاخر"

        return format_user_display_name(
            user,
            fallback="کاربر تفاخر",
            first_name_only=(privacy_mode == PhysicalCopy.Privacy.FIRST_NAME_ONLY),
        )

    @staticmethod
    def _enqueue_bot_notification(user, text: str) -> None:
        """
        Asynchronously creates BotTask for Telegram and Bale without blocking HTTP response (skill: bot-task-queue).
        """
        if not user:
            return
        try:
            from apps.notes.models import BotTask
            if getattr(user, "telegram_chat_id", None):
                BotTask.objects.create(
                    action="send",
                    platform="telegram",
                    chat_id=user.telegram_chat_id,
                    text=text,
                    bot_token=getattr(user, "telegram_bot_token", None) or "",
                )
            if getattr(user, "bale_chat_id", None):
                BotTask.objects.create(
                    action="send",
                    platform="bale",
                    chat_id=user.bale_chat_id,
                    text=text,
                    bot_token=getattr(user, "bale_bot_token", None) or "",
                )
        except Exception as e:
            logger.warning("Failed to enqueue bot task for user %s: %s", getattr(user, 'id', None), e)

    @classmethod
    def _finalize_handover_inventory(
        cls,
        copy: PhysicalCopy,
        recipient_user,
        handover_qty: int = 1,
        acquired_label: str = "",
        gifted_by=None,
    ) -> None:
        """
        Deducts handed-over quantity from the previous holder's shelf & linked donation item
        (issuing a fresh QR copy if remaining donated copies remain), and creates or updates
        the recipient's personal shelf entry.
        """
        from ..models.catalog import Item
        from ..models.shelf import UserShelfBook

        qty = max(1, int(handover_qty or 1))
        linked_items = list(
            Item.objects.select_for_update().filter(
                physical_copy=copy,
                deal_type=Item.DealType.DONATION,
                status=Item.Status.AVAILABLE,
            )
        )
        existing_linked = UserShelfBook.all_objects.select_for_update().filter(physical_copy=copy).first()

        if existing_linked and recipient_user and existing_linked.user_id == recipient_user.id and not existing_linked.is_deleted:
            for item in linked_items:
                item.status = Item.Status.COMPLETED
                item.stock = 0
                item.save(update_fields=["status", "stock", "updated_at"])
            existing_linked.disposition = UserShelfBook.Disposition.KEEPING
            existing_linked.donation_methods = []
            existing_linked.preferred_station = None
            existing_linked.save(
                update_fields=["disposition", "donation_methods", "preferred_station", "updated_at"]
            )
            return

        if existing_linked:
            if existing_linked.is_deleted:
                for item in linked_items:
                    item.status = Item.Status.COMPLETED
                    item.stock = 0
                    item.physical_copy = None
                    item.save(update_fields=["status", "stock", "physical_copy", "updated_at"])
                existing_linked.physical_copy = None
                existing_linked.save(update_fields=["physical_copy", "updated_at"])
            else:
                remaining_shelf = max(0, (existing_linked.quantity or 1) - qty)
                primary_item = linked_items[0] if linked_items else None
                remaining_stock = (
                    min(remaining_shelf, max(0, primary_item.stock - qty))
                    if primary_item
                    else 0
                )

                if primary_item and remaining_stock > 0 and remaining_shelf > 0:
                    next_copy = cls.register_physical_copy(
                        user=existing_linked.user,
                        book_title_id=copy.book_title_id,
                        condition=copy.condition,
                        privacy=copy.privacy,
                    )
                    primary_item.stock = remaining_stock
                    primary_item.physical_copy = next_copy
                    primary_item.save(update_fields=["stock", "physical_copy", "updated_at"])
                    for extra in linked_items[1:]:
                        extra.status = Item.Status.COMPLETED
                        extra.stock = 0
                        extra.physical_copy = None
                        extra.save(update_fields=["status", "stock", "physical_copy", "updated_at"])

                    existing_linked.quantity = remaining_shelf
                    existing_linked.physical_copy = next_copy
                    existing_linked.save(update_fields=["quantity", "physical_copy", "updated_at"])
                else:
                    for item in linked_items:
                        item.status = Item.Status.COMPLETED
                        item.stock = 0
                        item.physical_copy = None
                        item.save(update_fields=["status", "stock", "physical_copy", "updated_at"])

                    existing_linked.quantity = remaining_shelf
                    existing_linked.physical_copy = None
                    existing_linked.marketplace_item = None
                    existing_linked.disposition = UserShelfBook.Disposition.KEEPING
                    existing_linked.donation_methods = []
                    existing_linked.preferred_station = None
                    existing_linked.save(
                        update_fields=[
                            "quantity",
                            "physical_copy",
                            "marketplace_item",
                            "disposition",
                            "donation_methods",
                            "preferred_station",
                            "updated_at",
                        ]
                    )
        else:
            for item in linked_items:
                new_stock = max(0, item.stock - qty)
                if new_stock > 0:
                    next_copy = cls.register_physical_copy(
                        user=item.seller,
                        book_title_id=copy.book_title_id,
                        condition=copy.condition,
                        privacy=copy.privacy,
                    )
                    item.stock = new_stock
                    item.physical_copy = next_copy
                    item.save(update_fields=["stock", "physical_copy", "updated_at"])
                else:
                    item.status = Item.Status.COMPLETED
                    item.stock = 0
                    item.physical_copy = None
                    item.save(update_fields=["status", "stock", "physical_copy", "updated_at"])

        if not recipient_user:
            return

        donor = gifted_by or (existing_linked.user if existing_linked else None) or copy.original_donor

        UserShelfBook.objects.create(
            user=recipient_user,
            book_title=copy.book_title,
            book_format=UserShelfBook.BookFormat.PHYSICAL,
            visibility=UserShelfBook.Visibility.PRIVATE,
            reading_status=UserShelfBook.ReadingStatus.IN_SHELF,
            disposition=UserShelfBook.Disposition.KEEPING,
            condition=copy.condition,
            quantity=qty,
            acquired_from=acquired_label or f"اهدا حضوری ({copy.short_code})",
            physical_copy=copy,
            is_gift=True,
            gifted_by=donor,
        )
