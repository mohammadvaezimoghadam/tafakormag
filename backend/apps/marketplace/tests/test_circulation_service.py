import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models.circulation import (
    BookTitle,
    BookStation,
    PhysicalCopy,
    Transfer,
    Badge,
    BadgeAward,
)
from ..models.location import Province, City
from ..services.circulation_service import CirculationService
from ..services.badge_service import BadgeService
from ..exceptions import (
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

User = get_user_model()


class CirculationServiceTests(TestCase):
    """
    Automated integration test suite for Tafakor Book Circulation & Kiosk Handover System.
    Validates anti-fraud guardrails (72h cooldown, daily limit), state transitions,
    station deposits/pickups, and gamification badge awards.
    """

    def setUp(self):
        # Seed default gamification badges
        BadgeService.ensure_default_badges_exist()

        # Create test users
        self.donor = User.objects.create_user(phone="09121111111", password="password123")
        self.donor.first_name = "علی"
        self.donor.last_name = "محمدی"
        self.donor.save()

        self.recipient = User.objects.create_user(phone="09122222222", password="password123")
        self.recipient.first_name = "سارا"
        self.recipient.last_name = "احمدی"
        self.recipient.save()

        self.third_user = User.objects.create_user(phone="09123333333", password="password123")
        self.third_user.first_name = "رضا"
        self.third_user.last_name = "کریمی"
        self.third_user.save()

        # Create location & station
        self.province = Province.objects.create(name="تهران")
        self.city = City.objects.create(province=self.province, name="تهران")
        self.station = BookStation.objects.create(
            name="ایستگاه تفاخر دانشگاه تهران",
            city=self.city,
            address_text="میدان انقلاب، سردر اصلی دانشگاه",
            capacity=2,
            is_active=True
        )

        # Register a book title
        self.book_title = CirculationService.register_book_title(
            user=self.donor,
            data={
                "title": "گلشن راز",
                "author": "شیخ محمود شبستری",
                "publisher": "انتشارات زوار",
                "category": "ادبیات و عرفان",
                "isbn": "978-964-401-123-4"
            }
        )

    def test_register_book_title_with_persian_normalization(self):
        """Tests that Arabic Yeh/Kaf and spacing are normalized canonical in BookTitle."""
        title_raw = "كتاب گلشن راز با اعراب"
        author_raw = "شیخ محمود شبستري"

        t1 = CirculationService.register_book_title(
            user=self.donor,
            data={"title": title_raw, "author": author_raw}
        )

        self.assertIn("ک", t1.normalized_title)
        self.assertNotIn("ك", t1.normalized_title)
        self.assertIn("ی", t1.normalized_author)
        self.assertNotIn("ي", t1.normalized_author)

        # Re-registering with different spacing/Arabic chars returns the same entity
        t2 = CirculationService.register_book_title(
            user=self.recipient,
            data={"title": "کتاب گلشن راز با اعراب", "author": "شیخ محمود شبستری"}
        )
        self.assertEqual(t1.id, t2.id)

    def test_register_physical_copy(self):
        """Tests physical copy generation with TK-XXXX short code format."""
        copy = CirculationService.register_physical_copy(
            user=self.donor,
            book_title_id=self.book_title.id,
            condition=PhysicalCopy.Condition.LIKE_NEW
        )

        self.assertTrue(copy.short_code.startswith("TK-"))
        self.assertEqual(copy.current_holder, self.donor)
        self.assertEqual(copy.original_donor, self.donor)
        self.assertEqual(copy.status, PhysicalCopy.Status.ACTIVE)
        self.assertEqual(copy.transfer_count, 0)

    def test_inspect_copy_by_code(self):
        """Tests inspecting a copy via direct code or full QR URL."""
        copy = CirculationService.register_physical_copy(
            user=self.donor,
            book_title_id=self.book_title.id
        )

        # Inspection by full URL
        raw_url = f"https://tafakormag.ir/b/{copy.short_code.lower()}/"
        result_donor = CirculationService.inspect_copy_by_code(self.donor, raw_url)
        self.assertTrue(result_donor["is_holder"])
        self.assertFalse(result_donor["can_claim"])

        # Inspection by prospective recipient
        result_recipient = CirculationService.inspect_copy_by_code(self.recipient, copy.short_code)
        self.assertFalse(result_recipient["is_holder"])
        self.assertTrue(result_recipient["can_claim"])

    def test_in_person_handover_scan_and_confirm_flow(self):
        """
        Tests primary in-person flow:
        Recipient scans QR -> submits claim -> Donor taps Confirm -> transfer completes & badge awarded.
        """
        copy = CirculationService.register_physical_copy(
            user=self.donor,
            book_title_id=self.book_title.id
        )

        # 1. Recipient scans & claims book
        transfer = CirculationService.claim_by_recipient(
            recipient_user=self.recipient,
            short_code=copy.short_code,
            recipient_note="خیلی ممنون از اهدای این کتاب عالی!"
        )
        copy.refresh_from_db()
        self.assertEqual(copy.status, PhysicalCopy.Status.TRANSFERRING)
        self.assertEqual(transfer.status, Transfer.Status.PENDING_DONOR)
        self.assertEqual(transfer.to_user, self.recipient)

        # 2. Donor taps Confirm
        confirmed_trf = CirculationService.confirm_handover(
            user=self.donor,
            transfer_id=transfer.id
        )

        copy.refresh_from_db()
        self.assertEqual(confirmed_trf.status, Transfer.Status.CONFIRMED)
        self.assertEqual(copy.current_holder, self.recipient)
        self.assertEqual(copy.status, PhysicalCopy.Status.ACTIVE)
        self.assertEqual(copy.transfer_count, 1)

        # 3. Verify gamification badge awarded to donor
        has_first_kindness_badge = BadgeAward.objects.filter(
            user=self.donor,
            badge__slug="first_book_donated"
        ).exists()
        self.assertTrue(has_first_kindness_badge)

    def test_in_person_handover_otp_fallback_flow(self):
        """
        Tests offline / SMS fallback handover using 4-digit temporary OTP.
        """
        copy = CirculationService.register_physical_copy(
            user=self.donor,
            book_title_id=self.book_title.id
        )

        # Donor initiates with OTP fallback
        transfer, otp_code = CirculationService.initiate_handover(
            donor_user=self.donor,
            short_code=copy.short_code,
            recipient_user=self.recipient,
            method=Transfer.Method.OTP_FALLBACK,
            donor_note="یادگاری از کتابخانه شخصی من"
        )
        self.assertIsNotNone(otp_code)
        self.assertEqual(len(otp_code), 4)

        # Confirm with wrong OTP -> raises InvalidOtpError
        with self.assertRaises(InvalidOtpError):
            CirculationService.confirm_handover(
                user=self.recipient,
                transfer_id=transfer.id,
                otp_code="9999"
            )

        # Confirm with correct OTP -> success
        confirmed_trf = CirculationService.confirm_handover(
            user=self.recipient,
            transfer_id=transfer.id,
            otp_code=otp_code
        )
        copy.refresh_from_db()
        self.assertEqual(confirmed_trf.status, Transfer.Status.CONFIRMED)
        self.assertEqual(copy.current_holder, self.recipient)

    def test_anti_fraud_cooldown_72h(self):
        """
        Tests ADR-009 72-hour cooldown preventing rapid circular churning back to prior holder.
        """
        copy = CirculationService.register_physical_copy(
            user=self.donor,
            book_title_id=self.book_title.id
        )

        # Complete handover: donor -> recipient
        trf = CirculationService.claim_by_recipient(self.recipient, copy.short_code)
        CirculationService.confirm_handover(self.donor, trf.id)

        copy.refresh_from_db()
        self.assertEqual(copy.current_holder, self.recipient)

        # Recipient attempts to immediately hand it back to donor -> must raise TransferCooldownActiveError
        with self.assertRaises(TransferCooldownActiveError):
            CirculationService.initiate_handover(
                donor_user=self.recipient,
                short_code=copy.short_code,
                recipient_user=self.donor
            )

        # Recipient attempts to claim back by donor -> must also raise TransferCooldownActiveError
        with self.assertRaises(TransferCooldownActiveError):
            CirculationService.claim_by_recipient(
                recipient_user=self.donor,
                short_code=copy.short_code
            )

    def test_anti_fraud_daily_transfer_limit(self):
        """
        Tests ADR-009: max 2 completed handovers per day for a single user.
        """
        # User registers 3 copies
        c1 = CirculationService.register_physical_copy(self.donor, self.book_title.id)
        c2 = CirculationService.register_physical_copy(self.donor, self.book_title.id)
        c3 = CirculationService.register_physical_copy(self.donor, self.book_title.id)

        # Complete handover 1
        t1 = CirculationService.claim_by_recipient(self.recipient, c1.short_code)
        CirculationService.confirm_handover(self.donor, t1.id)

        # Complete handover 2
        t2 = CirculationService.claim_by_recipient(self.third_user, c2.short_code)
        CirculationService.confirm_handover(self.donor, t2.id)

        # Handover 3 on same day must be rejected by daily cap
        with self.assertRaises(DailyTransferLimitExceededError):
            CirculationService.initiate_handover(
                donor_user=self.donor,
                short_code=c3.short_code,
                recipient_user=self.recipient
            )

    def test_public_station_deposit_and_pickup(self):
        """
        Tests physical kiosk / station deposit and pickup flow.
        """
        copy = CirculationService.register_physical_copy(self.donor, self.book_title.id)

        # Deposit into station
        copy, trf_deposit = CirculationService.deposit_to_station(
            user=self.donor,
            short_code=copy.short_code,
            station_id=self.station.id,
            donor_note="برای دانشجویان عزیز در قفسه تفاخر قرار داده شد."
        )

        copy.refresh_from_db()
        self.assertEqual(copy.status, PhysicalCopy.Status.IN_STATION)
        self.assertIsNone(copy.current_holder)
        self.assertEqual(copy.station, self.station)
        self.assertEqual(trf_deposit.method, Transfer.Method.STATION_DEPOSIT)

        # Another user picks up from station
        copy, trf_pickup = CirculationService.pickup_from_station(
            user=self.recipient,
            short_code=copy.short_code,
            recipient_note="از قفسه دانشگاه برداشتم، متشکرم!"
        )

        copy.refresh_from_db()
        self.assertEqual(copy.status, PhysicalCopy.Status.ACTIVE)
        self.assertEqual(copy.current_holder, self.recipient)
        self.assertIsNone(copy.station)
        self.assertEqual(trf_pickup.method, Transfer.Method.STATION_PICKUP)

    def test_station_capacity_limit(self):
        """Tests that depositing into a full station raises StationFullError."""
        # Station capacity is 2
        c1 = CirculationService.register_physical_copy(self.donor, self.book_title.id)
        c2 = CirculationService.register_physical_copy(self.donor, self.book_title.id)
        c3 = CirculationService.register_physical_copy(self.donor, self.book_title.id)

        CirculationService.deposit_to_station(self.donor, c1.short_code, self.station.id)
        CirculationService.deposit_to_station(self.donor, c2.short_code, self.station.id)

        with self.assertRaises(StationFullError):
            CirculationService.deposit_to_station(self.donor, c3.short_code, self.station.id)

    def test_copy_journey_with_privacy(self):
        """
        Tests book movement journey timeline with FIRST_NAME_ONLY and ANONYMOUS privacy settings.
        """
        copy = CirculationService.register_physical_copy(
            user=self.donor,
            book_title_id=self.book_title.id,
            privacy=PhysicalCopy.Privacy.FIRST_NAME_ONLY
        )

        # Handover 1: donor -> recipient
        t1 = CirculationService.claim_by_recipient(self.recipient, copy.short_code)
        CirculationService.confirm_handover(self.donor, t1.id)

        # Handover 2: recipient -> third_user
        t2 = CirculationService.claim_by_recipient(self.third_user, copy.short_code)
        CirculationService.confirm_handover(self.recipient, t2.id)

        journey_data = CirculationService.get_copy_journey(copy.short_code)
        self.assertEqual(journey_data["total_transfers"], 2)
        events = journey_data["journey"]
        self.assertEqual(len(events), 2)

        # In FIRST_NAME_ONLY mode:
        self.assertEqual(events[0]["from_display_name"], "علی")
        self.assertEqual(events[0]["to_display_name"], "سارا")
        self.assertEqual(events[1]["from_display_name"], "سارا")
        self.assertEqual(events[1]["to_display_name"], "رضا")

    def test_privacy_never_exposes_phone_for_nameless_users(self):
        User = self.donor.__class__
        nameless = User.objects.create_user(phone="09129998877", password="password123")
        self.assertEqual(nameless.get_full_name(), "09129998877")

        self.assertEqual(
            CirculationService._format_user_privacy(nameless, PhysicalCopy.Privacy.PUBLIC_NAME),
            "کاربر تفاخر",
        )
        self.assertEqual(
            CirculationService._format_user_privacy(nameless, PhysicalCopy.Privacy.FIRST_NAME_ONLY),
            "کاربر تفاخر",
        )


