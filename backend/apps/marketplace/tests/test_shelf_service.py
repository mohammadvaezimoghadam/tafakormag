from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.serializers import UserSerializer
from ..models.catalog import Category, Item
from ..models.circulation import BookStation, BookTitle, PhysicalCopy
from ..models.location import City, Province
from ..models.shelf import UserShelfBook

User = get_user_model()


class UserShelfBookTests(TestCase):
    """
    Comprehensive tests for Personal Bookshelf (قفسه کتاب من):
    - Registering physical/digital books without forcing donation/sale or file upload
    - Privacy boundaries (private vs public shelf + no phone/note leakage)
    - Reading status updates and Persian-normalized search
    - Optional conversions to QR circulation, marketplace donation, and sale
    - Withdrawal back to personal keeping and anti-corruption guards
    - Constant SQL query count (zero N+1)
    """

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(phone="09121110001", password="password123")
        self.owner.first_name = "زهرا"
        self.owner.last_name = "احمدی"
        self.owner.save()

        self.other_user = User.objects.create_user(phone="09122220002", password="password123")
        self.other_user.first_name = "رضا"
        self.other_user.save()

        self.category = Category.objects.create(name="ادبیات", slug="literature", is_active=True)

    def test_add_physical_and_digital_books_without_offering_or_upload(self):
        """User can register physical and digital books solely for personal keeping."""
        self.client.force_authenticate(user=self.owner)

        res_phys = self.client.post(
            "/api/v1/marketplace/shelf/",
            {
                "title": "منطق‌الطیر",
                "author": "عطار نیشابوری",
                "publisher": "انتشارات علمی",
                "book_format": "physical",
                "reading_status": "reading",
                "quantity": 3,
                "condition": "good",
                "personal_note": "بخش هفت شهر عشق فوق‌العاده است",
                "rating": 5,
            },
            format="json",
        )
        self.assertEqual(res_phys.status_code, status.HTTP_201_CREATED)
        phys_data = res_phys.json()
        self.assertEqual(phys_data["disposition"], "keeping")
        self.assertEqual(phys_data["quantity"], 3)
        self.assertNotIn("visibility", phys_data)
        self.assertEqual(phys_data["reading_status"], "reading")
        self.assertIsNotNone(phys_data["physical_copy_summary"])
        self.assertIsNone(phys_data["marketplace_item_summary"])

        # Digital listing without any uploaded file (even if legacy client passes visibility='public')
        res_dig = self.client.post(
            "/api/v1/marketplace/shelf/",
            {
                "title": "كيمياگر",  # Arabic Kaf/Yeh to test normalization search
                "author": "پائولو كوئليو",
                "book_format": "digital",
                "visibility": "public",
                "reading_status": "finished",
                "digital_reference": "EPUB در تبلت شخصی",
            },
            format="json",
        )
        self.assertEqual(res_dig.status_code, status.HTTP_201_CREATED)
        dig_data = res_dig.json()
        self.assertEqual(dig_data["book_format"], "digital")
        self.assertEqual(dig_data["quantity"], 1)
        self.assertIsNone(dig_data["condition"])
        self.assertEqual(dig_data["digital_reference"], "EPUB در تبلت شخصی")
        self.assertEqual(UserShelfBook.objects.get(id=dig_data["id"]).visibility, UserShelfBook.Visibility.PRIVATE)

        # Profile serializer reflects exact total copy count (3 + 1 = 4)
        self.assertEqual(UserSerializer(self.owner).data["shelf_books_count"], 4)

        # Normalized Persian search finds Arabic-letter entry
        search_res = self.client.get("/api/v1/marketplace/shelf/?search=کیمیاگر")
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(search_res.json()), 1)
        self.assertEqual(search_res.json()[0]["id"], dig_data["id"])

        # Summary endpoint works in single query
        with self.assertNumQueries(1):
            sum_res = self.client.get("/api/v1/marketplace/shelf/summary/")
        self.assertEqual(sum_res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sum_res.json(),
            {
                "total": 2,
                "total_copies": 4,
                "reading_count": 1,
                "finished_count": 1,
                "want_to_read_count": 0,
                "keeping_count": 2,
                "offering_count": 0,
            },
        )

    def test_personal_shelf_strict_privacy_isolation(self):
        """All personal shelf books are strictly private; public shelf route is removed."""
        title_a = BookTitle.objects.create(title="گلشن راز", author="شبستری")
        title_b = BookTitle.objects.create(title="نهج‌البلاغه", author="سید رضی")

        private_entry = UserShelfBook.objects.create(
            user=self.owner,
            book_title=title_a,
            visibility=UserShelfBook.Visibility.PRIVATE,
            personal_note="یادداشت محرمانه",
        )
        legacy_public_entry = UserShelfBook.objects.create(
            user=self.owner,
            book_title=title_b,
            visibility=UserShelfBook.Visibility.PUBLIC,
            personal_note="یادداشت محرمانه قدیمی",
            digital_reference="فایل خصوصی من",
        )

        # Anonymous cannot list, retrieve, or hit legacy public shelf endpoint
        self.assertEqual(self.client.get("/api/v1/marketplace/shelf/").status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.client.get(f"/api/v1/marketplace/shelf/{legacy_public_entry.id}/").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/marketplace/shelf/public/?user_id={self.owner.id}").status_code,
            status.HTTP_404_NOT_FOUND,
        )

        # Other user cannot retrieve or mutate any shelf book (even legacy visibility=public rows)
        self.client.force_authenticate(user=self.other_user)
        self.assertEqual(
            self.client.get(f"/api/v1/marketplace/shelf/{private_entry.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/marketplace/shelf/{legacy_public_entry.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

        other_pub_patch = self.client.patch(
            f"/api/v1/marketplace/shelf/{legacy_public_entry.id}/",
            {"reading_status": "finished"},
            format="json",
        )
        self.assertEqual(other_pub_patch.status_code, status.HTTP_404_NOT_FOUND)

        other_del = self.client.delete(f"/api/v1/marketplace/shelf/{legacy_public_entry.id}/")
        self.assertEqual(other_del.status_code, status.HTTP_404_NOT_FOUND)

    def test_optional_circulation_donation_sale_and_withdraw_lifecycle(self):
        """Shelf book starts as personal keeping, can convert to QR/donation/sale, and withdraw back."""
        self.client.force_authenticate(user=self.owner)

        create_res = self.client.post(
            "/api/v1/marketplace/shelf/",
            {
                "title": "آیین دوستیابی",
                "author": "دیل کارنگی",
                "book_format": "physical",
                "condition": "good",
            },
            format="json",
        )
        shelf_id = create_res.json()["id"]

        # 1. Start QR circulation
        circ_res = self.client.post(f"/api/v1/marketplace/shelf/{shelf_id}/start-circulation/", {}, format="json")
        self.assertEqual(circ_res.status_code, status.HTTP_200_OK)
        short_code = circ_res.json()["physical_copy_summary"]["short_code"]
        self.assertTrue(short_code.startswith("TK-"))
        self.assertEqual(circ_res.json()["disposition"], "circulating")

        # 2. Withdraw back to personal keeping (retires QR copy cleanly)
        wd_res = self.client.post(f"/api/v1/marketplace/shelf/{shelf_id}/withdraw-offering/", {}, format="json")
        self.assertEqual(wd_res.status_code, status.HTTP_200_OK)
        self.assertEqual(wd_res.json()["disposition"], "keeping")
        self.assertEqual(wd_res.json()["physical_copy_summary"]["status"], PhysicalCopy.Status.RETIRED)

        # 3. Re-enrolling reuses same physical copy / short_code instead of creating duplicates
        circ_res2 = self.client.post(f"/api/v1/marketplace/shelf/{shelf_id}/start-circulation/", {}, format="json")
        self.assertEqual(circ_res2.status_code, status.HTTP_200_OK)
        self.assertEqual(circ_res2.json()["physical_copy_summary"]["short_code"], short_code)

        # 4. Publish to marketplace for SALE -> validates condition mapping ('good' -> 'used')
        sale_res = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/publish-listing/",
            {
                "deal_type": "sale",
                "price": 150000,
                "category_id": self.category.id,
            },
            format="json",
        )
        self.assertEqual(sale_res.status_code, status.HTTP_200_OK)
        sale_data = sale_res.json()
        self.assertEqual(sale_data["disposition"], "for_sale")
        item = Item.objects.get(id=sale_data["marketplace_item_summary"]["id"])
        self.assertEqual(item.status, Item.Status.AVAILABLE)
        self.assertEqual(item.condition, Item.Condition.USED)
        self.assertEqual(item.price, Decimal("150000"))
        self.assertEqual(item.book_detail.author, "دیل کارنگی")

        # Visible in public catalog
        cat_res = self.client.get("/api/v1/marketplace/items/?search=کارنگی")
        self.assertEqual(cat_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cat_res.json()), 1)

        # 5. Switch to DONATION -> updates item price to 0
        don_res = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/publish-listing/",
            {"deal_type": "donation", "price": 50000},
            format="json",
        )
        self.assertEqual(don_res.status_code, status.HTTP_200_OK)
        self.assertEqual(don_res.json()["disposition"], "for_donation")
        item.refresh_from_db()
        self.assertEqual(item.deal_type, Item.DealType.DONATION)
        self.assertEqual(item.price, Decimal("0"))

        # 6. Withdraw again -> item becomes ARCHIVED
        wd_res2 = self.client.post(f"/api/v1/marketplace/shelf/{shelf_id}/withdraw-offering/", {}, format="json")
        self.assertEqual(wd_res2.status_code, status.HTTP_200_OK)
        self.assertEqual(wd_res2.json()["disposition"], "keeping")
        item.refresh_from_db()
        self.assertEqual(item.status, Item.Status.ARCHIVED)

    def test_digital_book_cannot_start_qr_circulation_and_list_is_constant_queries(self):
        """Digital shelf entries block physical QR circulation and list uses constant queries."""
        self.client.force_authenticate(user=self.owner)
        res = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "مقدمه ابن خلدون", "author": "ابن خلدون", "book_format": "digital"},
            format="json",
        )
        shelf_id = res.json()["id"]

        bad_circ = self.client.post(f"/api/v1/marketplace/shelf/{shelf_id}/start-circulation/", {}, format="json")
        self.assertEqual(bad_circ.status_code, status.HTTP_400_BAD_REQUEST)

        # Add multiple more books to ensure list query count does NOT scale with N
        for idx in range(5):
            bt = BookTitle.objects.create(title=f"کتاب نمونه {idx}", author="نویسنده")
            UserShelfBook.objects.create(user=self.owner, book_title=bt)

        # DRF token auth + main select_related list query stays constant (<= 3 queries even with 6 rows)
        with self.assertNumQueries(1):
            list_res = self.client.get("/api/v1/marketplace/shelf/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.json()), 6)

    def test_donation_methods_in_person_postal_station_digital_and_catalog_filters(self):
        """
        Donations support explicit handover methods (in_person with QR copy, postal, station, digital),
        filter accurately on /items/?deal_type=donation&donation_method=..., and keep SQL queries constant.
        """
        province = Province.objects.create(name="تهران")
        city = City.objects.create(province=province, name="تهران")
        station = BookStation.objects.create(
            name="قفسه بوستان لاله",
            city=city,
            address_text="ضلع شمالی پارک لاله",
            capacity=30,
            is_active=True,
        )

        self.client.force_authenticate(user=self.owner)

        # A) Physical book with BOTH in_person (QR) and postal methods
        s_in_person = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "گلستان سعدی", "author": "سعدی", "book_format": "physical", "condition": "like_new"},
            format="json",
        ).json()["id"]
        pub_a = self.client.post(
            f"/api/v1/marketplace/shelf/{s_in_person}/publish-listing/",
            {
                "deal_type": "donation",
                "donation_methods": ["in_person", "postal"],
                "shipping_payer": "donor",
                "category_id": self.category.id,
            },
            format="json",
        )
        self.assertEqual(pub_a.status_code, status.HTTP_200_OK)
        pub_a_data = pub_a.json()
        self.assertEqual(pub_a_data["disposition"], "for_donation")
        self.assertEqual(pub_a_data["donation_methods"], ["in_person", "postal"])
        self.assertEqual(pub_a_data["shipping_payer"], "donor")
        self.assertIsNotNone(pub_a_data["physical_copy_summary"])
        short_code_a = pub_a_data["physical_copy_summary"]["short_code"]
        self.assertEqual(pub_a_data["physical_copy_summary"]["status"], PhysicalCopy.Status.ACTIVE)

        # B) Station donation with immediate deposit
        s_station = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "بوستان سعدی", "author": "سعدی", "book_format": "physical"},
            format="json",
        ).json()["id"]
        pub_b = self.client.post(
            f"/api/v1/marketplace/shelf/{s_station}/publish-listing/",
            {
                "deal_type": "donation",
                "donation_methods": ["station"],
                "station_id": station.id,
                "deposit_now": True,
                "category_id": self.category.id,
            },
            format="json",
        )
        self.assertEqual(pub_b.status_code, status.HTTP_200_OK)
        self.assertEqual(pub_b.json()["donation_methods"], ["station"])
        self.assertEqual(pub_b.json()["physical_copy_summary"]["status"], PhysicalCopy.Status.IN_STATION)

        # C) Digital book donation -> forced to ["digital"]
        s_digital = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "مناجات نامه", "author": "خواجه عبدالله انصاری", "book_format": "digital"},
            format="json",
        ).json()["id"]
        pub_c = self.client.post(
            f"/api/v1/marketplace/shelf/{s_digital}/publish-listing/",
            {
                "deal_type": "donation",
                "donation_methods": ["postal"],
                "category_id": self.category.id,
            },
            format="json",
        )
        self.assertEqual(pub_c.status_code, status.HTTP_200_OK)
        self.assertEqual(pub_c.json()["donation_methods"], ["digital"])

        # Catalog filtering by donation_method with constant query count (items + cover prefetch = 2 queries)
        self.client.force_authenticate(user=None)
        with self.assertNumQueries(2):
            all_res = self.client.get("/api/v1/marketplace/items/?deal_type=donation")
        self.assertEqual(all_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_res.json()), 3)

        in_person_res = self.client.get("/api/v1/marketplace/items/?deal_type=donation&donation_method=in_person").json()
        self.assertEqual(len(in_person_res), 1)
        self.assertEqual(in_person_res[0]["physical_copy_summary"]["short_code"], short_code_a)

        postal_res = self.client.get("/api/v1/marketplace/items/?deal_type=donation&donation_method=postal").json()
        self.assertEqual(len(postal_res), 1)
        self.assertEqual(postal_res[0]["title"], "گلستان سعدی")

        station_res = self.client.get("/api/v1/marketplace/items/?deal_type=donation&donation_method=station").json()
        self.assertEqual(len(station_res), 1)
        self.assertEqual(station_res[0]["station_summary"]["name"], "قفسه بوستان لاله")

        digital_res = self.client.get("/api/v1/marketplace/items/?deal_type=donation&donation_method=digital").json()
        self.assertEqual(len(digital_res), 1)
        self.assertEqual(digital_res[0]["title"], "مناجات نامه")

        # D) Completing an in-person QR handover marks the tied donation item completed
        #    and transfers shelf/copy ownership cleanly to the recipient
        self.client.force_authenticate(user=self.other_user)
        claim = self.client.post(
            "/api/v1/marketplace/copies/handover/claim/",
            {"short_code": short_code_a, "recipient_note": "سپاس بابت هدیه زیبا"},
            format="json",
        )
        self.assertEqual(claim.status_code, status.HTTP_200_OK)
        transfer_id = claim.json()["id"]

        self.client.force_authenticate(user=self.owner)
        confirm = self.client.post(
            f"/api/v1/marketplace/copies/handover/{transfer_id}/confirm/",
            {"donor_note": "امیدوارم از خواندنش لذت ببرید"},
            format="json",
        )
        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm.json()["donor_note"], "امیدوارم از خواندنش لذت ببرید")
        self.assertEqual(confirm.json()["recipient_note"], "سپاس بابت هدیه زیبا")
        item_a = Item.objects.get(id=pub_a_data["marketplace_item_summary"]["id"])
        self.assertEqual(item_a.status, Item.Status.COMPLETED)
        self.assertEqual(item_a.stock, 0)

        owner_shelf = UserShelfBook.objects.get(id=s_in_person)
        self.assertIsNone(owner_shelf.physical_copy_id)
        self.assertEqual(owner_shelf.disposition, UserShelfBook.Disposition.KEEPING)
        self.assertEqual(owner_shelf.quantity, 0)

        self.client.force_authenticate(user=self.other_user)
        recipient_shelf = self.client.get("/api/v1/marketplace/shelf/").json()
        self.assertEqual(len(recipient_shelf), 1)
        self.assertEqual(recipient_shelf[0]["book_title"]["title"], "گلستان سعدی")
        self.assertEqual(recipient_shelf[0]["physical_copy_summary"]["short_code"], short_code_a)
        self.assertEqual(recipient_shelf[0]["disposition"], "keeping")

        # Book disappears from active public donations list once handed over
        self.client.force_authenticate(user=None)
        remaining_in_person = self.client.get("/api/v1/marketplace/items/?deal_type=donation&donation_method=in_person").json()
        self.assertEqual(len(remaining_in_person), 0)

    def test_multi_copy_shelf_donation_and_partial_in_person_handovers(self):
        """
        Registering 3 copies allows donating 2 copies (`stock=2`), validating stock <= quantity,
        handing over 1 copy first (auto-issuing a fresh QR code for the 2nd donated copy),
        and completing the 2nd copy leaves 1 personal copy on the donor's shelf.
        """
        self.client.force_authenticate(user=self.owner)
        create_res = self.client.post(
            "/api/v1/marketplace/shelf/",
            {
                "title": "قصه‌های خوب برای بچه‌های خوب",
                "author": "مهدی آذر یزدی",
                "book_format": "physical",
                "quantity": 3,
                "condition": "like_new",
            },
            format="json",
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        shelf_id = create_res.json()["id"]
        self.assertEqual(create_res.json()["quantity"], 3)

        # Cannot publish more copies for donation than owned on shelf
        bad_pub = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/publish-listing/",
            {
                "deal_type": "donation",
                "donation_methods": ["in_person"],
                "stock": 4,
            },
            format="json",
        )
        self.assertEqual(bad_pub.status_code, status.HTTP_400_BAD_REQUEST)

        # Donate 2 of the 3 copies for in-person handover
        pub_res = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/publish-listing/",
            {
                "deal_type": "donation",
                "donation_methods": ["in_person"],
                "stock": 2,
            },
            format="json",
        )
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        pub_data = pub_res.json()
        self.assertEqual(pub_data["quantity"], 3)
        self.assertEqual(pub_data["marketplace_item_summary"]["stock"], 2)
        first_code = pub_data["physical_copy_summary"]["short_code"]

        # Recipient inspects first QR code -> sees available_quantity == 2
        self.client.force_authenticate(user=self.other_user)
        inspect_1 = self.client.get(f"/api/v1/marketplace/copies/inspect/?code={first_code}")
        self.assertEqual(inspect_1.status_code, status.HTTP_200_OK)
        self.assertEqual(inspect_1.json()["available_quantity"], 2)

        # Claiming 3 copies (> 2) fails
        bad_claim = self.client.post(
            "/api/v1/marketplace/copies/handover/claim/",
            {"short_code": first_code, "quantity": 3},
            format="json",
        )
        self.assertEqual(bad_claim.status_code, status.HTTP_400_BAD_REQUEST)

        # Claim 1 copy & confirm handover
        claim_1 = self.client.post(
            "/api/v1/marketplace/copies/handover/claim/",
            {"short_code": first_code, "quantity": 1, "recipient_note": "یک جلد تحویل گرفتم"},
            format="json",
        )
        self.assertEqual(claim_1.status_code, status.HTTP_200_OK)
        self.assertEqual(claim_1.json()["quantity"], 1)
        trf1_id = claim_1.json()["id"]

        self.client.force_authenticate(user=self.owner)
        confirm_1 = self.client.post(
            f"/api/v1/marketplace/copies/handover/{trf1_id}/confirm/",
            {},
            format="json",
        )
        self.assertEqual(confirm_1.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_1.json()["quantity"], 1)

        # Donor still has 2 total copies on shelf, 1 copy remaining in active donation, and a fresh QR code
        owner_shelf_res = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(owner_shelf_res["quantity"], 2)
        self.assertEqual(owner_shelf_res["disposition"], "for_donation")
        self.assertEqual(owner_shelf_res["marketplace_item_summary"]["stock"], 1)
        second_code = owner_shelf_res["physical_copy_summary"]["short_code"]
        self.assertNotEqual(second_code, first_code)

        # Second partial handover via OTP fallback finishes the remaining donated copy
        init_2 = self.client.post(
            "/api/v1/marketplace/copies/handover/initiate/",
            {"short_code": second_code, "method": "otp_fallback", "quantity": 1},
            format="json",
        )
        self.assertEqual(init_2.status_code, status.HTTP_201_CREATED)
        otp_code = init_2.json()["otp_code"]
        trf2_id = init_2.json()["id"]

        self.client.force_authenticate(user=self.other_user)
        confirm_2 = self.client.post(
            f"/api/v1/marketplace/copies/handover/{trf2_id}/confirm/",
            {"otp_code": otp_code},
            format="json",
        )
        self.assertEqual(confirm_2.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_2.json()["quantity"], 1)

        # Donor keeps their remaining 1 personal copy and item is completed
        self.client.force_authenticate(user=self.owner)
        owner_after = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(owner_after["quantity"], 1)
        self.assertEqual(owner_after["disposition"], "keeping")
        self.assertIsNone(owner_after["marketplace_item_summary"])
        self.assertIsNone(owner_after["physical_copy_summary"])

    def test_publish_shelf_book_to_topic_creates_atomic_post_and_serializes_in_chat(self):
        """
        Publishing a shelf book to a topic atomically creates a Post in that topic,
        and querying the topic's posts returns post.book_donation with full metadata.
        """
        from apps.notes.models import Topic, Post

        topic = Topic.objects.create(name="تاپیک کتاب‌خوانی مشهد", created_by=self.owner)

        self.client.force_authenticate(user=self.owner)
        res = self.client.post(
            "/api/v1/marketplace/shelf/",
            {
                "title": "دیوان شمس تبریزی",
                "author": "مولانا جلال‌الدین محمد بلخی",
                "publisher": "انتشارات ققنوس",
                "condition": "good",
                "quantity": 1,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        shelf_id = res.json()["id"]

        # Publish to the topic for donation
        pub_res = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/publish-listing/",
            {
                "deal_type": "donation",
                "topic_id": topic.id,
                "donation_methods": ["in_person", "postal"],
                "shipping_payer": "recipient",
            },
            format="json",
        )
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)

        # Assert post was created in the topic
        post = Post.objects.filter(topic=topic).latest("created_at")
        self.assertIn("اهدای کتاب: دیوان شمس تبریزی", post.content)
        self.assertEqual(post.author, self.owner)

        # Assert post has linked book_item
        self.assertIsNotNone(post.book_item)
        self.assertEqual(post.book_item.title, "دیوان شمس تبریزی")

        # Query posts API and check book_donation in response
        posts_res = self.client.get(f"/api/notes/?topic={topic.id}")
        self.assertEqual(posts_res.status_code, status.HTTP_200_OK)
        results = posts_res.json().get("results", posts_res.json())
        self.assertEqual(len(results), 1)
        post_data = results[0]
        self.assertIn("book_donation", post_data)
        book_donation = post_data["book_donation"]
        self.assertIsNotNone(book_donation)
        self.assertEqual(book_donation["title"], "دیوان شمس تبریزی")
        self.assertEqual(book_donation["author"], "مولانا جلال‌الدین محمد بلخی")
        self.assertIn("in_person", book_donation["donation_methods"])
        self.assertEqual(book_donation["deal_type"], "donation")

    def test_donate_to_phone_and_confirm_receipt(self):
        """Tests full phone donation flow: stock reservation, lazy QR creation, confirm receipt, and blocked re-donation."""
        self.client.force_authenticate(user=self.owner)

        # 1. Add book with 3 copies
        res = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "شاهنامه فردوسی", "author": "ابوالقاسم فردوسی", "quantity": 3},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        shelf_id = res.json()["id"]

        # 2. Donate 2 copies to other_user's phone
        res_donate = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/donate-to-phone/",
            {"quantity": 2, "recipient_phone": self.other_user.phone, "send_sms": False},
            format="json",
        )
        self.assertEqual(res_donate.status_code, status.HTTP_200_OK)
        donate_data = res_donate.json()
        transfer_id = donate_data["transfer_id"]
        self.assertIsNotNone(donate_data["short_code"])
        self.assertEqual(donate_data["quantity"], 2)

        # 3. Check donor's shelf: quantity=3, reserved_quantity=2, available_quantity=1
        donor_shelf = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(donor_shelf["quantity"], 3)
        self.assertEqual(donor_shelf["reserved_quantity"], 2)
        self.assertEqual(donor_shelf["available_quantity"], 1)

        # 4. Check recipient's incoming gifts
        self.client.force_authenticate(user=self.other_user)
        res_gifts = self.client.get("/api/v1/marketplace/shelf/incoming-gifts/")
        self.assertEqual(res_gifts.status_code, status.HTTP_200_OK)
        gifts = res_gifts.json()
        self.assertEqual(len(gifts), 1)
        self.assertEqual(gifts[0]["id"], transfer_id)
        self.assertEqual(gifts[0]["quantity"], 2)

        # 5. Recipient confirms receipt
        res_confirm = self.client.post(
            "/api/v1/marketplace/shelf/confirm-gift/",
            {"transfer_id": transfer_id},
            format="json",
        )
        self.assertEqual(res_confirm.status_code, status.HTTP_200_OK)

        # 6. Check recipient's shelf: has 2 copies, is_gift=True, can_donate=False, can_edit=False, can_delete=False
        recip_shelf_list = self.client.get("/api/v1/marketplace/shelf/").json()
        shelf_entries = recip_shelf_list.get("results", recip_shelf_list) if isinstance(recip_shelf_list, dict) else recip_shelf_list
        self.assertEqual(len(shelf_entries), 1)
        entry = shelf_entries[0]
        self.assertEqual(entry["quantity"], 2)
        self.assertTrue(entry["is_gift"])
        self.assertFalse(entry["can_donate"])
        self.assertFalse(entry["can_edit"])
        self.assertFalse(entry["can_delete"])
        self.assertEqual(entry["gifted_by_name"], "زهرا احمدی")

        # 6.1 Verify recipient CANNOT edit gifted book
        res_edit = self.client.patch(
            f"/api/v1/marketplace/shelf/{entry['id']}/",
            {"reading_status": "finished"},
            format="json",
        )
        self.assertEqual(res_edit.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("کتاب‌های هدیه‌گرفته‌شده قابل ویرایش نیستند", res_edit.json()["detail"])

        # 6.2 Verify recipient CANNOT delete gifted book
        res_del = self.client.delete(f"/api/v1/marketplace/shelf/{entry['id']}/")
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("کتاب‌های هدیه‌گرفته‌شده قابل حذف از قفسه نیستند", res_del.json()["detail"])

        # 7. Check donor's shelf: quantity=1, reserved_quantity=0, available_quantity=1
        self.client.force_authenticate(user=self.owner)
        donor_shelf_after = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(donor_shelf_after["quantity"], 1)
        self.assertEqual(donor_shelf_after["reserved_quantity"], 0)
        self.assertEqual(donor_shelf_after["available_quantity"], 1)

    def test_donate_to_unregistered_phone_and_cancel_gift(self):
        """Tests donating to an unregistered phone number and donor cancelling before confirmation."""
        self.client.force_authenticate(user=self.owner)

        res = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "گلستان سعدی", "author": "سعدی شیرازی", "quantity": 1},
            format="json",
        )
        shelf_id = res.json()["id"]

        # Donate to non-existent phone
        res_donate = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/donate-to-phone/",
            {"quantity": 1, "recipient_phone": "09990008877", "send_sms": False},
            format="json",
        )
        self.assertEqual(res_donate.status_code, status.HTTP_200_OK)
        transfer_id = res_donate.json()["transfer_id"]

        # Donor cancels gift
        res_cancel = self.client.post(
            "/api/v1/marketplace/shelf/cancel-gift/",
            {"transfer_id": transfer_id},
            format="json",
        )
        self.assertEqual(res_cancel.status_code, status.HTTP_200_OK)

        # Donor available quantity restored
        shelf_after = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(shelf_after["quantity"], 1)
        self.assertEqual(shelf_after["reserved_quantity"], 0)
        self.assertEqual(shelf_after["available_quantity"], 1)

    def test_admin_user_search_endpoint(self):
        """Tests the admin-restricted user search endpoint by phone, name, and normalized text."""
        admin = User.objects.create_user(phone="09120000001", password="password123")
        admin.is_staff = True
        admin.first_name = "علی"
        admin.last_name = "اکبری"
        admin.save()

        # Non-staff receives 403
        self.client.force_authenticate(user=self.owner)
        res_forbidden = self.client.get("/api/v1/accounts/users/search/?q=رضا")
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # Staff can search
        self.client.force_authenticate(user=admin)

        # Search by phone
        res_phone = self.client.get("/api/v1/accounts/users/search/?q=0912222")
        self.assertEqual(res_phone.status_code, status.HTTP_200_OK)
        results = res_phone.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["phone"], "09122220002")
        self.assertEqual(results[0]["full_name"], "رضا")

        # Search with Arabic/Persian normalization
        res_name = self.client.get("/api/v1/accounts/users/search/?q=زهرا")
        self.assertEqual(res_name.status_code, status.HTTP_200_OK)
        results = res_name.json()
        self.assertTrue(any(u["id"] == self.owner.id for u in results))

    def test_direct_admin_donation_to_existing_user(self):
        """Tests staff direct instant delivery to an existing user with zero recipient friction."""
        admin = User.objects.create_user(phone="09120000002", password="password123")
        admin.is_staff = True
        admin.first_name = "مدیر"
        admin.last_name = "تفکر"
        admin.save()

        self.client.force_authenticate(user=admin)
        res_create = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "داستان راستان", "author": "شهید مطهری", "quantity": 10},
            format="json",
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        shelf_id = res_create.json()["id"]

        # Admin donates 2 copies to self.owner
        res_donate = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/admin-donate/",
            {"quantity": 2, "recipient_phone": self.owner.phone},
            format="json",
        )
        self.assertEqual(res_donate.status_code, status.HTTP_200_OK)
        data = res_donate.json()
        self.assertEqual(data["status"], "confirmed")
        self.assertEqual(data["quantity"], 2)
        self.assertTrue(data["recipient_registered"])

        # Check admin inventory decremented
        admin_shelf = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(admin_shelf["quantity"], 8)
        self.assertEqual(admin_shelf["reserved_quantity"], 0)

        # Check recipient shelf: instant delivery with is_gift=True
        self.client.force_authenticate(user=self.owner)
        res_recipient = self.client.get("/api/v1/marketplace/shelf/").json()
        recipient_books = res_recipient if isinstance(res_recipient, list) else res_recipient.get("results", [])
        gifted_book = next((b for b in recipient_books if b["book_title"]["title"] == "داستان راستان"), None)
        self.assertIsNotNone(gifted_book)
        self.assertTrue(gifted_book["is_gift"])
        self.assertEqual(gifted_book["quantity"], 2)
        self.assertEqual(gifted_book["gifted_by_name"], "مدیر تفکر")
        self.assertFalse(gifted_book["can_donate"])
        self.assertFalse(gifted_book["can_edit"])
        self.assertFalse(gifted_book["can_delete"])

    def test_admin_donation_to_unregistered_phone_and_auto_claim_on_signup(self):
        """Tests admin donation to an unregistered phone and auto-claim upon registration."""
        admin = User.objects.create_user(phone="09120000003", password="password123")
        admin.is_staff = True
        admin.save()

        self.client.force_authenticate(user=admin)
        res_create = self.client.post(
            "/api/v1/marketplace/shelf/",
            {"title": "جاذبه و دافعه علی (ع)", "author": "شهید مطهری", "quantity": 5},
            format="json",
        )
        shelf_id = res_create.json()["id"]

        # Admin donates to unregistered phone
        new_phone = "09359998877"
        res_donate = self.client.post(
            f"/api/v1/marketplace/shelf/{shelf_id}/admin-donate/",
            {"quantity": 1, "recipient_phone": new_phone},
            format="json",
        )
        self.assertEqual(res_donate.status_code, status.HTTP_200_OK)
        data = res_donate.json()
        self.assertEqual(data["status"], "pending_recipient")
        self.assertFalse(data["recipient_registered"])
        self.assertTrue(data["sms_sent"])

        # Admin stock reserved
        admin_shelf = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(admin_shelf["quantity"], 5)
        self.assertEqual(admin_shelf["reserved_quantity"], 1)
        self.assertEqual(admin_shelf["available_quantity"], 4)

        # New user signs up with that phone
        new_user = User.objects.create_user(phone=new_phone, password="password123")

        # Auto-claim signal executed on save!
        self.client.force_authenticate(user=new_user)
        res_user_shelf = self.client.get("/api/v1/marketplace/shelf/").json()
        user_books = res_user_shelf if isinstance(res_user_shelf, list) else res_user_shelf.get("results", [])
        claimed_book = next((b for b in user_books if b["book_title"]["title"] == "جاذبه و دافعه علی (ع)"), None)
        self.assertIsNotNone(claimed_book)
        self.assertTrue(claimed_book["is_gift"])
        self.assertEqual(claimed_book["quantity"], 1)

        # Admin stock deducted from total and reserved
        self.client.force_authenticate(user=admin)
        admin_shelf_after = self.client.get(f"/api/v1/marketplace/shelf/{shelf_id}/").json()
        self.assertEqual(admin_shelf_after["quantity"], 4)
        self.assertEqual(admin_shelf_after["reserved_quantity"], 0)

    def test_admin_donations_report_endpoint(self):
        """Tests the admin donations audit report endpoint."""
        admin = User.objects.create_user(phone="09120000004", password="password123")
        admin.is_staff = True
        admin.save()

        # Non-staff receives 403
        self.client.force_authenticate(user=self.owner)
        res_forbidden = self.client.get("/api/v1/marketplace/shelf/admin-donations-report/")
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # Staff receives list of donations
        self.client.force_authenticate(user=admin)
        res_report = self.client.get("/api/v1/marketplace/shelf/admin-donations-report/")
        self.assertEqual(res_report.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res_report.json(), list)




