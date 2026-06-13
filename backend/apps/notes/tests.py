from django.test import TestCase
from django.db import IntegrityError
from apps.accounts.models import User, MessagingTarget
from apps.notes.models import Topic, Post, PostReaction, PostComment, BotTask


class NotesModelTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            phone="09123456789"
        )
        # Create another test user for comment/reactions
        self.other_user = User.objects.create_user(
            phone="09123456780"
        )
        
        # Create a test topic
        self.topic = Topic.objects.create(
            name="تاپیک تستی",
            description="توضیحات تاپیک تستی",
            created_by=self.user,
            telegram_bot_active=True,
            bale_bot_active=False
        )

        # Create a messaging target
        self.target = MessagingTarget.objects.create(
            user=self.user,
            chat_id="123456789",
            label="گروه تلگرام",
            platform="telegram"
        )
        self.topic.telegram_connections.add(self.target)

    def test_topic_creation_and_string_representation(self):
        """Test Topic model creation and __str__ method."""
        self.assertEqual(str(self.topic), "تاپیک تستی")
        self.assertEqual(self.topic.created_by, self.user)
        self.assertTrue(self.topic.telegram_bot_active)
        self.assertFalse(self.topic.bale_bot_active)
        self.assertEqual(self.topic.telegram_connections.count(), 1)
        self.assertEqual(self.topic.telegram_connections.first(), self.target)

    def test_post_creation_and_string_representation(self):
        """Test Post model creation, choices, default values and __str__ method."""
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="## عنوان پست\nمحتوای آزمایشی",
            media_type="text"
        )
        expected_str = f"Post by {self.user.phone} in {self.topic.name} at {post.created_at}"
        self.assertEqual(str(post), expected_str)
        self.assertEqual(post.media_type, "text")
        self.assertEqual(post.telegram_message_ids, {})
        self.assertEqual(post.bale_message_ids, {})

    def test_post_ordering(self):
        """Test that posts are ordered by -created_at by default."""
        post1 = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست اول"
        )
        post2 = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست دوم"
        )
        posts = Post.objects.filter(topic=self.topic)
        # Ordering is -created_at, so post2 should be first
        self.assertEqual(list(posts), [post2, post1])

    def test_post_reaction_creation_and_unique_constraint(self):
        """Test PostReaction model creation, __str__ and uniqueness constraint."""
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست تستی برای ری‌اکشن"
        )
        reaction = PostReaction.objects.create(
            post=post,
            user=self.other_user,
            emoji="👍"
        )
        self.assertEqual(str(reaction), f"{self.other_user.phone} reacted 👍 on Post {post.id}")
        
        # Test unique constraint (same user cannot react multiple times to the same post)
        with self.assertRaises(IntegrityError):
            PostReaction.objects.create(
                post=post,
                user=self.other_user,
                emoji="❤️"
            )

    def test_post_comment_creation_and_ordering(self):
        """Test PostComment model creation, __str__ and ordering by created_at."""
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست تستی برای کامنت"
        )
        comment1 = PostComment.objects.create(
            post=post,
            user=self.other_user,
            content="کامنت اول"
        )
        comment2 = PostComment.objects.create(
            post=post,
            user=self.user,
            content="کامنت دوم"
        )
        
        self.assertEqual(str(comment1), f"Comment by {self.other_user.phone} on Post {post.id}")
        
        # Comments should be ordered by created_at (ascending)
        comments = PostComment.objects.filter(post=post)
        self.assertEqual(list(comments), [comment1, comment2])

    def test_bot_task_creation_and_string_representation(self):
        """Test BotTask creation, default values and __str__ method."""
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست تستی برای تسک ربات"
        )
        task = BotTask.objects.create(
            action="send",
            platform="telegram",
            chat_id="123456789",
            text="ارسال پست تستی",
            post_id=post,
            bot_token="test_token"
        )
        self.assertEqual(str(task), "BotTask(send, telegram, processed=False)")
        self.assertFalse(task.processed)
        self.assertEqual(task.post_id, post)
