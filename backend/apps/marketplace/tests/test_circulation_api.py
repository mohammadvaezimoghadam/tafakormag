from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from ..models.circulation import (
    BookTitle,
    BookStation,
    PhysicalCopy,
    Transfer,
    Badge,
    BadgeAward,
)
from ..models.location import Province, City
from ..services.badge_service import BadgeService

User = get_user_model()


class CirculationAPITests(TestCase):
    """
    Integration tests for Book Circulation & In-Person Handover REST API endpoints.
    Verifies thin viewsets, authentication guards, and response formatting.
    """

    def setUp(self):
        BadgeService.ensure_default_badges_exist()
        self.client = APIClient()

        self.donor = User.objects.create_user(phone="09121111111", password="password123")
        self.donor.first_name = "علی"
        self.donor.save()

        self.recipient = User.objects.create_user(phone="09122222222", password="password123")
        self.recipient.first_name = "سارا"
        self.recipient.save()

        self.province = Province.objects.create(name="تهران")
        self.city = City.objects.create(province=self.province, name="تهران")
        self.station = BookStation.objects.create(
            name="قفسه مهربانی مترو تئاتر شهر",
            city=self.city,
            address_text="ایستگاه تقاطعی خط ۳ و ۴، سالن اصلی",
            capacity=10,
            is_active=True
        )

        self.book_title = BookTitle.objects.create(
            title="گلشن راز",
            author="شیخ محمود شبستری",
            publisher="انتشارات زوار"
        )

    def test_book_title_create_and_search_api(self):
        """Authenticated user registers new title and searches with Persian normalization."""
        self.client.force_authenticate(user=self.donor)
        response = self.client.post("/api/v1/marketplace/book-titles/", {
            "title": "كتاب مثنوي معنوي",  # Arabic Kaf and Yeh
            "author": "مولانا جلال‌الدين محمد بلخي",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["title"], "كتاب مثنوي معنوي")

        # Public search with standard Persian characters
        self.client.force_authenticate(user=None)
        search_res = self.client.get("/api/v1/marketplace/book-titles/?q=مثنوی")
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        results = search_res.json()
        self.assertGreaterEqual(len(results), 1)

    def test_register_and_inspect_physical_copy_api(self):
        """User registers physical copy, then prospective reader inspects it."""
        self.client.force_authenticate(user=self.donor)
        reg_res = self.client.post("/api/v1/marketplace/copies/register/", {
            "book_title_id": self.book_title.id,
            "condition": "good",
            "privacy": "first_name_only"
        })
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        short_code = reg_res.json()["short_code"]
        self.assertTrue(short_code.startswith("TK-"))

        # Prospective recipient scans the QR code / inspects
        self.client.force_authenticate(user=self.recipient)
        insp_res = self.client.get(f"/api/v1/marketplace/copies/inspect/?code={short_code}")
        self.assertEqual(insp_res.status_code, status.HTTP_200_OK)
        insp_data = insp_res.json()
        self.assertFalse(insp_data["is_holder"])
        self.assertTrue(insp_data["can_claim"])
        self.assertEqual(insp_data["available_quantity"], 1)
        self.assertEqual(insp_data["book_title"]["title"], "گلشن راز")

    def test_complete_in_person_handover_via_api(self):
        """
        Complete end-to-end API flow:
        1. Donor registers copy
        2. Recipient scans & claims
        3. Donor confirms with one tap
        4. Recipient checks journey timeline & my-books
        """
        self.client.force_authenticate(user=self.donor)
        reg_res = self.client.post("/api/v1/marketplace/copies/register/", {
            "book_title_id": self.book_title.id,
        })
        short_code = reg_res.json()["short_code"]

        # Recipient claims
        self.client.force_authenticate(user=self.recipient)
        claim_res = self.client.post("/api/v1/marketplace/copies/handover/claim/", {
            "short_code": short_code,
            "recipient_note": "بسیار سپاسگزارم"
        })
        self.assertEqual(claim_res.status_code, status.HTTP_200_OK)
        transfer_id = claim_res.json()["id"]

        # Donor confirms
        self.client.force_authenticate(user=self.donor)
        confirm_res = self.client.post(f"/api/v1/marketplace/copies/handover/{transfer_id}/confirm/", {})
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_res.json()["status"], "confirmed")

        # Recipient views my-books
        self.client.force_authenticate(user=self.recipient)
        my_books_res = self.client.get("/api/v1/marketplace/copies/my-books/")
        self.assertEqual(my_books_res.status_code, status.HTTP_200_OK)
        held = my_books_res.json()
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["short_code"], short_code)

        # Public journey check
        self.client.force_authenticate(user=None)
        journey_res = self.client.get(f"/api/v1/marketplace/copies/journey/?code={short_code}")
        self.assertEqual(journey_res.status_code, status.HTTP_200_OK)
        journey_data = journey_res.json()
        self.assertEqual(journey_data["total_transfers"], 1)
        self.assertEqual(len(journey_data["journey"]), 1)
        self.assertEqual(journey_data["journey"][0]["from_display_name"], "علی")
        self.assertEqual(journey_data["journey"][0]["to_display_name"], "سارا")
        self.assertEqual(journey_data["journey"][0]["quantity"], 1)

    def test_station_deposit_and_pickup_api(self):
        """User deposits into station via API and another user picks it up."""
        self.client.force_authenticate(user=self.donor)
        reg_res = self.client.post("/api/v1/marketplace/copies/register/", {
            "book_title_id": self.book_title.id,
        })
        short_code = reg_res.json()["short_code"]

        # Deposit
        dep_res = self.client.post("/api/v1/marketplace/copies/station/deposit/", {
            "short_code": short_code,
            "station_id": self.station.id,
            "donor_note": "هدیه به مسافران مترو"
        })
        self.assertEqual(dep_res.status_code, status.HTTP_200_OK)

        # Check station books
        self.client.force_authenticate(user=None)
        st_books_res = self.client.get(f"/api/v1/marketplace/book-stations/{self.station.id}/books/")
        self.assertEqual(st_books_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(st_books_res.json()), 1)

        # Pickup by recipient
        self.client.force_authenticate(user=self.recipient)
        pick_res = self.client.post("/api/v1/marketplace/copies/station/pickup/", {
            "short_code": short_code,
            "recipient_note": "کتاب را از ایستگاه برداشتم"
        })
        self.assertEqual(pick_res.status_code, status.HTTP_200_OK)

    def test_phone_assignment_requires_registered_user_and_shows_in_incoming(self):
        """
        Handover via recipient_phone enforces registered Tafakor user, normalizes Persian digits,
        cancels stale open OTP session cleanly, and appears in recipient's /handover/incoming/ list.
        """
        self.client.force_authenticate(user=self.donor)
        reg_res = self.client.post("/api/v1/marketplace/copies/register/", {
            "book_title_id": self.book_title.id,
        })
        short_code = reg_res.json()["short_code"]

        # Unregistered phone fails clearly
        bad_res = self.client.post("/api/v1/marketplace/copies/handover/initiate/", {
            "short_code": short_code,
            "method": "scan_confirm",
            "recipient_phone": "09998887766",
        })
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Donor starts an open OTP session (for simultaneous QR + OTP view)
        otp_init = self.client.post("/api/v1/marketplace/copies/handover/initiate/", {
            "short_code": short_code,
            "method": "otp_fallback",
            "quantity": 1,
        })
        self.assertEqual(otp_init.status_code, status.HTTP_201_CREATED)

        # Donor switches smoothly to registered recipient phone in Persian numerals (no block from stale OTP)
        phone_init = self.client.post("/api/v1/marketplace/copies/handover/initiate/", {
            "short_code": short_code,
            "method": "scan_confirm",
            "recipient_phone": "۰۹۱۲۲۲۲۲۲۲۲",
            "donor_note": "هدیه مستقیم",
        })
        self.assertEqual(phone_init.status_code, status.HTTP_201_CREATED)
        transfer_id = phone_init.json()["id"]

        # Recipient sees it immediately in /handover/incoming/ with 1-query efficiency and confirms in 1 tap
        self.client.force_authenticate(user=self.recipient)
        inc_res = self.client.get("/api/v1/marketplace/copies/handover/incoming/")
        self.assertEqual(inc_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(inc_res.json()), 1)
        self.assertEqual(inc_res.json()[0]["id"], transfer_id)
        self.assertEqual(inc_res.json()[0]["copy_short_code"], short_code)

        confirm_res = self.client.post(f"/api/v1/marketplace/copies/handover/{transfer_id}/confirm/", {})
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_res.json()["status"], "confirmed")

        # Incoming list is empty once confirmed
        self.assertEqual(len(self.client.get("/api/v1/marketplace/copies/handover/incoming/").json()), 0)

    def test_recipient_claim_converts_open_otp_transfer_to_donor_tap_confirm(self):
        """
        When donor has an open QR/OTP handover screen, a recipient claiming via short_code alone
        converts it cleanly to PENDING_DONOR so donor confirms in 1 tap without needing OTP.
        """
        self.client.force_authenticate(user=self.donor)
        reg_res = self.client.post("/api/v1/marketplace/copies/register/", {
            "book_title_id": self.book_title.id,
        })
        short_code = reg_res.json()["short_code"]

        init_res = self.client.post("/api/v1/marketplace/copies/handover/initiate/", {
            "short_code": short_code,
            "method": "otp_fallback",
        })
        self.assertEqual(init_res.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.recipient)
        claim_res = self.client.post("/api/v1/marketplace/copies/handover/claim/", {
            "short_code": short_code,
            "recipient_note": "اسکن حضوری",
        })
        self.assertEqual(claim_res.status_code, status.HTTP_200_OK)
        self.assertEqual(claim_res.json()["status"], "pending_donor")
        self.assertEqual(claim_res.json()["method"], "scan_confirm")

        self.client.force_authenticate(user=self.donor)
        confirm_res = self.client.post(
            f"/api/v1/marketplace/copies/handover/{claim_res.json()['id']}/confirm/",
            {},
        )
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_res.json()["status"], "confirmed")

