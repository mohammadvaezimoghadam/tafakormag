import time
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apps.notes.models import Topic, Post, PostReaction, PostComment, BotTask
from apps.accounts.models import MessagingTarget

User = get_user_model()

@pytest.mark.django_db
class TestNotesAPIIntegration:
    """
    Integration tests for notes-related endpoints (Topics, Posts, Comments, Reactions)
    and automatic BotTask generation.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        # 1. Create two test users
        self.user1 = User.objects.create_user(phone="09111111111", password="testpassword1")
        self.token1 = Token.objects.create(user=self.user1)

        self.user2 = User.objects.create_user(phone="09222222222", password="testpassword2")
        self.token2 = Token.objects.create(user=self.user2)

        # 2. Clients setup
        self.client1 = APIClient()
        self.client1.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        self.client2 = APIClient()
        self.client2.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")

        self.anon_client = APIClient()

    # --- TOPIC TESTS ---
    def test_create_topic_success(self):
        payload = {"name": "Test Topic 1", "description": "Topic description"}
        response = self.client1.post("/api/notes/topics/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Topic 1"
        assert response.data["created_by"] == self.user1.id

    def test_create_topic_unauthenticated_fails(self):
        payload = {"name": "Test Topic 1"}
        response = self.anon_client.post("/api/notes/topics/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_topic_only_by_creator(self):
        topic = Topic.objects.create(name="Topic A", created_by=self.user1)
        payload = {"name": "Topic A Edited"}
        
        # User 2 (not creator) attempts to update
        response = self.client2.patch(f"/api/notes/topics/{topic.id}/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # User 1 (creator) updates successfully
        response = self.client1.patch(f"/api/notes/topics/{topic.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Topic A Edited"

    def test_topic_post_badge_create_and_update(self):
        # 1. Create topic with post_badge
        payload = {"name": "Topic Badge Test", "description": "Desc", "post_badge": "@my_badge"}
        response = self.client1.post("/api/notes/topics/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["post_badge"] == "@my_badge"
        topic_id = response.data["id"]

        # 2. Update post_badge
        update_payload = {"post_badge": "@updated_badge"}
        res_update = self.client1.patch(f"/api/notes/topics/{topic_id}/", update_payload, format="json")
        assert res_update.status_code == status.HTTP_200_OK
        assert res_update.data["post_badge"] == "@updated_badge"

    def test_delete_topic_only_by_creator(self):
        topic = Topic.objects.create(name="Topic A", created_by=self.user1)
        
        # User 2 attempts to delete
        response = self.client2.delete(f"/api/notes/topics/{topic.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # User 1 deletes successfully
        response = self.client1.delete(f"/api/notes/topics/{topic.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Topic.objects.filter(id=topic.id).exists()

    # --- POST TESTS & BOT SYNC ---
    def test_create_post_only_by_topic_creator(self):
        topic = Topic.objects.create(name="Topic A", created_by=self.user1)
        payload = {"topic": topic.id, "content": "Hello world from post"}

        # User 2 (not creator of topic) attempts to post
        response = self.client2.post("/api/notes/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # User 1 posts successfully
        response = self.client1.post("/api/notes/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify topic description updated
        topic.refresh_from_db()
        assert topic.description == "Hello world from post"

    def test_post_creation_triggers_bot_tasks(self):
        # Configure user 1 with bot token
        self.user1.telegram_bot_token = "12345:telegram-token"
        self.user1.save()

        # Create topic and activate telegram bot
        topic = Topic.objects.create(name="Topic A", created_by=self.user1, telegram_bot_active=True)
        
        # Create messaging target (destination) for user 1
        target = MessagingTarget.objects.create(user=self.user1, platform="telegram", chat_id="999888", label="My Channel", is_active=True)
        topic.telegram_connections.add(target)

        # Create post
        payload = {"topic": topic.id, "content": "Testing bot dispatch"}
        response = self.client1.post("/api/notes/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # Verify BotTask created
        tasks = BotTask.objects.filter(post_id=response.data["id"])
        assert tasks.count() == 1
        task = tasks.first()
        assert task.action == "send"
        assert task.platform == "telegram"
        assert task.chat_id == "999888"
        assert task.text == "Testing bot dispatch"
        assert task.bot_token == "12345:telegram-token"

    def test_post_creation_appends_topic_post_badge_to_bot_task(self):
        # Configure user 1 with bot token
        self.user1.telegram_bot_token = "12345:telegram-token"
        self.user1.save()

        # Create topic with post_badge and activate telegram bot
        topic = Topic.objects.create(
            name="Topic With Badge",
            post_badge="@my_badge_channel",
            created_by=self.user1,
            telegram_bot_active=True
        )
        
        target = MessagingTarget.objects.create(
            user=self.user1,
            platform="telegram",
            chat_id="777666",
            label="Badge Channel",
            is_active=True
        )
        topic.telegram_connections.add(target)

        # Create post
        payload = {"topic": topic.id, "content": "Important Announcement"}
        response = self.client1.post("/api/notes/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "Important Announcement\n\n@my_badge_channel"

        # Verify BotTask text includes badge
        task = BotTask.objects.filter(post_id=response.data["id"]).first()
        assert task is not None
        assert task.text == "Important Announcement\n\n@my_badge_channel"

    def test_post_edit_triggers_edit_bot_task(self):
        # Set up bot, connections and post
        self.user1.telegram_bot_token = "12345:telegram-token"
        self.user1.save()
        topic = Topic.objects.create(name="Topic A", created_by=self.user1, telegram_bot_active=True)
        target = MessagingTarget.objects.create(user=self.user1, platform="telegram", chat_id="999888", label="My Channel", is_active=True)
        topic.telegram_connections.add(target)
        
        post = Post.objects.create(topic=topic, author=self.user1, content="Original content", telegram_message_ids={"999888": "101"})

        # Edit post
        payload = {"content": "Updated content"}
        response = self.client1.patch(f"/api/notes/{post.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Verify BotTask for edit is created
        task = BotTask.objects.filter(post_id=post.id).latest("id")
        assert task.action == "edit"
        assert task.platform == "telegram"
        assert task.chat_id == "999888"
        assert task.text == "Updated content"
        assert task.message_id == "101"

    def test_post_delete_triggers_delete_bot_task(self):
        # Set up bot, connections and post
        self.user1.telegram_bot_token = "12345:telegram-token"
        self.user1.save()
        topic = Topic.objects.create(name="Topic A", created_by=self.user1, telegram_bot_active=True)
        target = MessagingTarget.objects.create(user=self.user1, platform="telegram", chat_id="999888", label="My Channel", is_active=True)
        topic.telegram_connections.add(target)
        post = Post.objects.create(topic=topic, author=self.user1, content="Original content", telegram_message_ids={"999888": "101"})

        # Delete post
        response = self.client1.delete(f"/api/notes/{post.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify BotTask for delete is created
        task = BotTask.objects.filter(note_id=post.id).latest("id")
        assert task.action == "delete"
        assert task.platform == "telegram"
        assert task.chat_id == "999888"
        assert task.message_id == "101"

    # --- COMMENTS & REACTIONS TESTS ---
    def test_comment_creation(self):
        topic = Topic.objects.create(name="Topic A", created_by=self.user1)
        post = Post.objects.create(topic=topic, author=self.user1, content="Test post content")

        # Get comments (initially empty)
        response = self.client1.get(f"/api/notes/{post.id}/comments/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

        # Post comment
        payload = {"content": "This is a comment"}
        response = self.client1.post(f"/api/notes/{post.id}/comments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "This is a comment"
        assert response.data["user_phone"] == "09111111111"

        # Anonymous cannot post comment
        response = self.anon_client.post(f"/api/notes/{post.id}/comments/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_reaction(self):
        topic = Topic.objects.create(name="Topic A", created_by=self.user1)
        post = Post.objects.create(topic=topic, author=self.user1, content="Test post content")

        # Send valid reaction
        payload = {"emoji": "👍"}
        response = self.client1.post(f"/api/notes/{post.id}/react/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["emoji"] == "👍"
        assert response.data["created"] is True

        # Send invalid reaction
        payload = {"emoji": "❌"}
        response = self.client1.post(f"/api/notes/{post.id}/react/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Remove reaction by sending empty emoji
        payload = {"emoji": ""}
        response = self.client1.post(f"/api/notes/{post.id}/react/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert not PostReaction.objects.filter(post=post, user=self.user1).exists()

    def test_topic_create_with_image(self):
        """
        Verify that a user can create a topic with an uploaded image file.
        """
        image_file = SimpleUploadedFile(
            "topic_test.jpg", b"fake_image_content", content_type="image/jpeg"
        )
        payload = {
            "name": "Topic with Image",
            "description": "Topic description with image",
            "image": image_file
        }
        response = self.client1.post("/api/notes/topics/", payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Topic with Image"
        assert response.data["image"] is not None
        assert "topic_test" in response.data["image"]

        # Verify database
        topic = Topic.objects.get(id=response.data["id"])
        assert topic.image.name.startswith("topic_images/topic_test")

    def test_post_create_with_media(self):
        """
        Verify that a user can create a post with an uploaded media file (e.g. image).
        """
        # Configure user 1 with bot token
        self.user1.telegram_bot_token = "12345:telegram-token"
        self.user1.save()

        # Create topic with telegram bot active
        topic = Topic.objects.create(name="Topic A", created_by=self.user1, telegram_bot_active=True)
        target = MessagingTarget.objects.create(user=self.user1, platform="telegram", chat_id="999888", label="My Channel", is_active=True)
        topic.telegram_connections.add(target)

        # Upload post with media_file
        media_file = SimpleUploadedFile(
            "post_test.jpg", b"fake_post_image_content", content_type="image/jpeg"
        )
        payload = {
            "topic": topic.id,
            "content": "Post with media",
            "media_type": "image",
            "media_file": media_file
        }
        response = self.client1.post("/api/notes/", payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["media_type"] == "image"
        assert response.data["media_file"] is not None
        assert "post_test" in response.data["media_file"]

        # Verify database
        post = Post.objects.get(id=response.data["id"])
        assert post.media_file.name.startswith("post_media/post_test")

        # Verify BotTask contains media information
        tasks = BotTask.objects.filter(post_id=post.id)
        assert tasks.count() == 1
        task = tasks.first()
        assert task.action == "send"
        assert task.platform == "telegram"
        assert task.chat_id == "999888"

        # Verify task detail API returns it (fetching via bot API credentials)
        bot_client = APIClient()
        from django.conf import settings
        bot_client.credentials(HTTP_X_BOT_API_KEY=settings.BOT_API_KEY)
        
        resp = bot_client.get("/api/bot/tasks/")
        assert resp.status_code == status.HTTP_200_OK
        task_data = next(t for t in resp.data if t["id"] == task.id)
        assert task_data["media_type"] == "image"
        assert task_data["media_url"] is not None
        assert "post_test" in task_data["media_url"]
