import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apps.notes.models import Topic
from apps.donations.models import DonationCampaign, DonationTransaction, TransparencyLog
from apps.donations import services

User = get_user_model()

@pytest.mark.django_db
class TestDonationsAPIIntegration:
    """
    Integration tests for Kindness & Donation API endpoints:
    - Campaign creation & listing with filters
    - Strict creator-only permission on update/delete
    - Transaction processing & metrics calculation
    - User profile donations_count integration
    - Transparency reports
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        # 1. Create two test users
        self.creator = User.objects.create_user(phone="09121111111", password="creatorpassword")
        self.creator.first_name = "Ali"
        self.creator.save()
        self.creator_token = Token.objects.create(user=self.creator)

        self.other_user = User.objects.create_user(phone="09122222222", password="otherpassword")
        self.other_user.first_name = "Reza"
        self.other_user.save()
        self.other_token = Token.objects.create(user=self.other_user)

        # 2. Setup API clients
        self.creator_client = APIClient()
        self.creator_client.credentials(HTTP_AUTHORIZATION=f"Token {self.creator_token.key}")

        self.other_client = APIClient()
        self.other_client.credentials(HTTP_AUTHORIZATION=f"Token {self.other_token.key}")

        self.anon_client = APIClient()

        # 3. Create a topic for campaigns
        self.topic = Topic.objects.create(name="Charity Topic", created_by=self.creator)

    # --- CAMPAIGN CREATION & LISTING ---
    def test_create_campaign_success(self):
        payload = {
            "topic": self.topic.id,
            "title": "مدرسه روستایی",
            "category": DonationCampaign.CategoryChoices.SCHOOL,
            "target_amount": 50000000,
            "description": "ساخت مدرسه دو کلاسه"
        }
        response = self.creator_client.post("/api/donations/campaigns/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "مدرسه روستایی"
        assert response.data["category"] == DonationCampaign.CategoryChoices.SCHOOL
        assert response.data["creator_info"]["phone"] == self.creator.phone

        # Verify DB record
        campaign = DonationCampaign.objects.get(id=response.data["id"])
        assert campaign.creator == self.creator
        assert campaign.topic == self.topic
        assert campaign.post is not None

    def test_create_campaign_unauthenticated_fails(self):
        payload = {
            "topic": self.topic.id,
            "title": "پویش تستی",
            "category": DonationCampaign.CategoryChoices.MOSQUE,
            "target_amount": 10000000,
            "description": "توضیحات پویش تستی"
        }
        response = self.anon_client.post("/api/donations/campaigns/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_campaigns_and_filter_by_category(self):
        # Create school campaign
        DonationCampaign.objects.create(
            creator=self.creator,
            topic=self.topic,
            title="کمک به مدرسه",
            description="توضیحات کمک به مدرسه",
            category=DonationCampaign.CategoryChoices.SCHOOL,
            target_amount=10000000
        )
        # Create treatment campaign
        DonationCampaign.objects.create(
            creator=self.creator,
            topic=self.topic,
            title="کمک درمانی",
            description="توضیحات کمک درمانی",
            category=DonationCampaign.CategoryChoices.TREATMENT,
            target_amount=20000000
        )

        # List all
        response = self.anon_client.get("/api/donations/campaigns/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # Filter by school category
        response_filtered = self.anon_client.get(f"/api/donations/campaigns/?category={DonationCampaign.CategoryChoices.SCHOOL}")
        assert response_filtered.status_code == status.HTTP_200_OK
        assert len(response_filtered.data) == 1
        assert response_filtered.data[0]["category"] == DonationCampaign.CategoryChoices.SCHOOL

    # --- STRICT PERMISSION TESTS (CREATOR ONLY) ---
    def test_update_campaign_strict_creator_permission(self):
        campaign = DonationCampaign.objects.create(
            creator=self.creator,
            topic=self.topic,
            title="پویش اولیه",
            description="توضیحات اولیه",
            category=DonationCampaign.CategoryChoices.LIVELIHOOD,
            target_amount=15000000
        )

        update_payload = {"title": "عنوان جدید توسط غیرسازنده"}
        
        # User 2 (not creator) attempts to update
        response_forbidden = self.other_client.patch(
            f"/api/donations/campaigns/{campaign.id}/", 
            update_payload, 
            format="json"
        )
        assert response_forbidden.status_code == status.HTTP_403_FORBIDDEN

        # Creator updates successfully
        creator_payload = {"title": "عنوان ویرایش شده توسط سازنده"}
        response_ok = self.creator_client.patch(
            f"/api/donations/campaigns/{campaign.id}/", 
            creator_payload, 
            format="json"
        )
        assert response_ok.status_code == status.HTTP_200_OK
        campaign.refresh_from_db()
        assert campaign.title == "عنوان ویرایش شده توسط سازنده"

    def test_delete_campaign_strict_creator_permission(self):
        campaign = DonationCampaign.objects.create(
            creator=self.creator,
            topic=self.topic,
            title="پویش حذفی",
            description="توضیحات حذفی",
            category=DonationCampaign.CategoryChoices.OTHER,
            target_amount=5000000
        )

        # Non-creator attempts to delete
        response_forbidden = self.other_client.delete(f"/api/donations/campaigns/{campaign.id}/")
        assert response_forbidden.status_code == status.HTTP_403_FORBIDDEN
        assert DonationCampaign.objects.filter(id=campaign.id).exists()

        # Creator deletes successfully
        response_ok = self.creator_client.delete(f"/api/donations/campaigns/{campaign.id}/")
        assert response_ok.status_code == status.HTTP_204_NO_CONTENT
        assert not DonationCampaign.objects.filter(id=campaign.id).exists()

    # --- TRANSACTION & METRICS TESTS ---
    def test_donate_transaction_success_updates_metrics(self):
        campaign = DonationCampaign.objects.create(
            creator=self.creator,
            topic=self.topic,
            title="توسعه مسجد",
            description="توضیحات ساخت و ساز مسجد",
            category=DonationCampaign.CategoryChoices.MOSQUE,
            target_amount=10000000
        )

        donate_payload = {
            "amount": 2500000,
            "is_anonymous": False
        }

        # 1. Other user initiates donation
        response = self.other_client.post(
            f"/api/donations/campaigns/{campaign.id}/donate/", 
            donate_payload, 
            format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "pending"
        assert response.data["amount"] == 2500000
        authority = response.data["authority"]

        # 2. Payment verification / settlement
        verify_payload = {
            "authority": authority,
            "gateway_ref": "GATEWAY_123456",
            "tracking_code": "TRACK_789"
        }
        res_verify = self.other_client.post("/api/donations/payment/verify/", verify_payload, format="json")
        assert res_verify.status_code == status.HTTP_200_OK
        assert res_verify.data["status"] == "success"

        # Verify campaign metrics updated
        campaign.refresh_from_db()
        assert campaign.collected_amount == 2500000
        assert campaign.donors_count == 1

    # --- USER PROFILE DONATIONS COUNT INTEGRATION ---
    def test_user_profile_donations_count(self):
        # 1. Creator has 1 campaign created
        campaign = DonationCampaign.objects.create(
            creator=self.creator,
            topic=self.topic,
            title="پویش کاربر ۱",
            description="توضیحات پویش اول",
            category=DonationCampaign.CategoryChoices.SCHOOL,
            target_amount=10000000
        )

        # 2. Other user makes 1 donation
        DonationTransaction.objects.create(
            campaign=campaign,
            donor=self.other_user,
            amount=1000000,
            status=DonationTransaction.PaymentStatus.SUCCESSFUL
        )

        # Check creator profile -> donations_count should be 1 (1 created)
        res_creator = self.creator_client.get("/api/auth/profile/")
        assert res_creator.status_code == status.HTTP_200_OK
        assert res_creator.data["donations_count"] == 1

        # Check other user profile -> donations_count should be 1 (1 transaction)
        res_other = self.other_client.get("/api/auth/profile/")
        assert res_other.status_code == status.HTTP_200_OK
        assert res_other.data["donations_count"] == 1

    # --- TRANSPARENCY REPORT ---
    def test_transparency_log_creation_and_listing(self):
        campaign = DonationCampaign.objects.create(
            creator=self.creator,
            topic=self.topic,
            title="گزارش شفافیت مسجد",
            description="توضیحات گزارش شفافیت",
            category=DonationCampaign.CategoryChoices.MOSQUE,
            target_amount=5000000
        )

        log_payload = {
            "title": "خرید سیمان و مصالح",
            "amount": 1500000,
            "description": "خرید ۱۰ کیسه سیمان برای ساخت و ساز"
        }

        # Non-creator cannot add transparency report
        res_forbidden = self.other_client.post(
            f"/api/donations/campaigns/{campaign.id}/transparency/", 
            log_payload, 
            format="json"
        )
        assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN

        # Creator adds report
        res_ok = self.creator_client.post(
            f"/api/donations/campaigns/{campaign.id}/transparency/", 
            log_payload, 
            format="json"
        )
        assert res_ok.status_code == status.HTTP_201_CREATED
        assert res_ok.data["title"] == "خرید سیمان و مصالح"
        assert res_ok.data["amount"] == 1500000

        # Public can view transparency logs through campaign detail endpoint
        res_detail = self.anon_client.get(f"/api/donations/campaigns/{campaign.id}/")
        assert res_detail.status_code == status.HTTP_200_OK
        assert len(res_detail.data["transparency_logs"]) == 1
        assert res_detail.data["transparency_logs"][0]["title"] == "خرید سیمان و مصالح"
        assert res_detail.data["transparency_logs"][0]["amount"] == 1500000
