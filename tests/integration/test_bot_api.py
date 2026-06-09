import uuid
import pytest
import responses
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from apps.accounts.models import BotConnectionToken, MessagingTarget

User = get_user_model()

@pytest.mark.django_db
class TestBotAPIIntegration:
    """
    Integration tests for bot-related endpoints.
    These tests execute Django views inside the test-runner process,
    connecting directly to the postgres-test database.
    """

    @pytest.fixture(autouse=True)
    def setup_client(self):
        self.client = APIClient()

    def test_register_phone_chat_creates_user_and_sets_chat_id(self):
        """
        Verify that hitting api/bot/register-phone-chat/ creates a user
        and registers their Telegram/Bale chat ID correctly.
        """
        payload = {
            "phone": "+989123456789",  # Should be normalized to 09123456789
            "platform": "telegram",
            "chat_id": "123456789"
        }
        
        # Call the endpoint
        response = self.client.post("/api/bot/register-phone-chat/", payload, format="json")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["created"] is True

        # Assert database state
        user = User.objects.get(phone="09123456789")
        assert user.telegram_chat_id == "123456789"
        assert user.bale_chat_id is None

    def test_verify_link_associates_token_and_sets_chat_id(self):
        """
        Verify that verifying a one-time connection token updates the user's
        chat ID and marks the token as used.
        """
        # Seed user and token
        user = User.objects.create_user(phone="09876543210")
        token = BotConnectionToken.objects.create(user=user, platform="telegram")

        payload = {
            "token": str(token.token),
            "platform": "telegram",
            "chat_id": "987654321"
        }

        response = self.client.post("/api/bot/verify-link/", payload, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify database
        user.refresh_from_db()
        token.refresh_from_db()
        
        assert user.telegram_chat_id == "987654321"
        assert token.is_used is True

    def test_register_destination_creates_messaging_target(self):
        """
        Verify registering a group or channel destination successfully
        creates a MessagingTarget database record.
        """
        user = User.objects.create_user(phone="09112223344")
        
        payload = {
            "user_id": user.id,
            "platform": "telegram",
            "chat_id": "-100199228833",  # Typical Telegram channel chat ID
            "label": "My Cool Channel"
        }
        
        response = self.client.post("/api/bot/register-destination/", payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["chat_id"] == "-100199228833"
        assert response.data["label"] == "My Cool Channel"

        # Verify database
        target = MessagingTarget.objects.get(user=user, platform="telegram")
        assert target.chat_id == "-100199228833"
        assert target.label == "My Cool Channel"
        assert target.is_default is True  # Should default to True if first one

    @responses.activate
    def test_update_custom_bot_mocks_external_telegram_call(self):
        """
        Verify updating a custom bot token.
        This views triggers a requests.get to the Telegram API which must be mocked.
        """
        # Create user and authenticate via token auth
        user = User.objects.create_user(phone="09334445566")
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        # Mock the external getMe request made by Django views.py
        bot_token = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
        mock_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        responses.add(
            responses.GET,
            mock_url,
            json={
                "ok": True,
                "result": {
                    "id": 999999,
                    "is_bot": True,
                    "first_name": "TestCustomBot",
                    "username": "test_custom_bot"
                }
            },
            status=200
        )

        payload = {
            "platform": "telegram",
            "token": bot_token
        }

        # Make request to the auth ViewSet action 'update-custom-bot'
        response = self.client.post("/api/auth/update-custom-bot/", payload, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["username"] == "@test_custom_bot"

        # Verify database state
        user.refresh_from_db()
        assert user.telegram_bot_token == bot_token
        assert user.telegram_bot_username == "@test_custom_bot"
