from unittest.mock import patch, MagicMock
from django.conf import settings
from django.test import TestCase
from django.db import IntegrityError
from apps.accounts.models import User, MessagingTarget
from apps.notes.models import Topic, Post, PostReaction, PostComment, BotTask, ImportTask, TopicAdmin, TopicFAQ


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
        """Test that posts are ordered by created_at and telegram_message_id by default."""
        post1 = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست اول",
            telegram_message_id=1
        )
        post2 = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست دوم",
            telegram_message_id=2
        )
        posts = Post.objects.filter(topic=self.topic)
        # Ordering is created_at, telegram_message_id, so post1 should be first
        self.assertEqual(list(posts), [post1, post2])

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


import tempfile
import json
import os
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.notes.services import process_telegram_json_import

class TelegramImportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09123456789", password="password")
        self.client.force_authenticate(user=self.user)
        self.topic = Topic.objects.create(name="تاپیک ایمپورت", created_by=self.user)
        
    def test_import_task_model_creation(self):
        task = ImportTask.objects.create(
            topic=self.topic,
            status='PENDING',
            current_stage='شروع',
            progress=0
        )
        self.assertEqual(task.status, 'PENDING')
        self.assertEqual(task.progress, 0)
        self.assertEqual(task.topic, self.topic)

    def test_process_telegram_json_import_service(self):
        # Create a mock result.json file
        mock_data = {
            "name": "Channel Name",
            "type": "public_channel",
            "id": 12345,
            "messages": [
                {
                    "id": 101,
                    "type": "message",
                    "date": "2023-06-01T15:30:00",
                    "text": "سلام دنیا! این یک پیام تستی تلگرام است."
                },
                {
                    "id": 102,
                    "type": "message",
                    "date": "2023-06-01T15:31:00",
                    "text": [
                        "پیام با فرمت ",
                        {"type": "bold", "text": "برجسته"},
                        " و ",
                        {"type": "link", "text": "گوگل", "href": "https://google.com"}
                    ]
                },
                {
                    "id": 103,
                    "type": "service",
                    "date": "2023-06-01T15:32:00",
                    "text": "Service message"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as temp_file:
            json.dump(mock_data, temp_file)
            temp_filepath = temp_file.name
            
        task = ImportTask.objects.create(
            topic=self.topic,
            status='PENDING',
            current_stage='pending',
            progress=0
        )
        
        # Run service function synchronously for testing
        process_telegram_json_import(str(task.id), temp_filepath)
        
        # Check task completion status
        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')
        self.assertEqual(task.progress, 100)
        
        # Check created posts in DB
        posts = Post.objects.filter(topic=self.topic)
        # Service messages are skipped, only 2 valid posts should be imported
        self.assertEqual(posts.count(), 2)
        
        # Check first post details
        post1 = posts.filter(telegram_message_id=101).first()
        self.assertIsNotNone(post1)
        self.assertTrue(post1.is_imported)
        self.assertEqual(post1.content, "سلام دنیا! این یک پیام تستی تلگرام است.")
        
        # Check second post details (Markdown rendering)
        post2 = posts.filter(telegram_message_id=102).first()
        self.assertIsNotNone(post2)
        self.assertEqual(post2.content, "پیام با فرمت **برجسته** و [گوگل](https://google.com)")

        # Verify no BotTasks were created for imported posts
        bot_tasks_count = BotTask.objects.filter(post_id__in=posts).count()
        self.assertEqual(bot_tasks_count, 0)
        
        # Verify temp file was cleaned up by service finally block
        self.assertFalse(os.path.exists(temp_filepath))


import zipfile
import io
from apps.notes.services import process_telegram_zip_import
from django.core.files.uploadedfile import SimpleUploadedFile


class TelegramZipImportServiceTests(APITestCase):
    """تست‌های مستقیم سرویس ZIP import"""

    def setUp(self):
        self.user = User.objects.create_user(phone="09111111111", password="password")
        self.client.force_authenticate(user=self.user)
        self.topic = Topic.objects.create(name="تاپیک ZIP تستی", created_by=self.user)

    def _make_zip_file(self, messages, include_result_json=True, corrupt_json=False, extra_files=None):
        """ساخت فایل ZIP تستی در حافظه"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            if include_result_json:
                if corrupt_json:
                    zf.writestr('result.json', 'THIS IS NOT JSON {{{')
                else:
                    data = {"name": "Test Channel", "type": "public_channel", "messages": messages}
                    zf.writestr('result.json', json.dumps(data, ensure_ascii=False))
            if extra_files:
                for path, content in extra_files.items():
                    zf.writestr(path, content)
        buf.seek(0)
        return buf.read()

    def _create_task_and_write_zip(self, zip_bytes):
        """ذخیره ZIP روی دیسک و ساخت ImportTask"""
        import uuid
        from django.conf import settings
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_imports')
        os.makedirs(temp_dir, exist_ok=True)
        filepath = os.path.join(temp_dir, f"test_{uuid.uuid4().hex}.zip")
        with open(filepath, 'wb') as f:
            f.write(zip_bytes)
        task = ImportTask.objects.create(topic=self.topic, status='PENDING', current_stage='pending', progress=0)
        return task, filepath

    # --- تست ۱: درون‌ریزی موفق پیام‌های متنی ---
    def test_zip_import_text_messages_success(self):
        messages = [
            {"id": 201, "type": "message", "date": "2024-01-15T10:00:00", "text": "پیام اول از ZIP"},
            {"id": 202, "type": "message", "date": "2024-01-15T10:01:00", "text": [
                "پیام ",
                {"type": "bold", "text": "فرمت‌دار"},
                " از ZIP"
            ]},
            {"id": 203, "type": "service", "date": "2024-01-15T10:02:00", "text": "service msg"},  # باید skip شود
        ]
        zip_bytes = self._make_zip_file(messages)
        task, filepath = self._create_task_and_write_zip(zip_bytes)

        process_telegram_zip_import(str(task.id), filepath)

        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')
        self.assertEqual(task.progress, 100)

        posts = Post.objects.filter(topic=self.topic, is_imported=True)
        self.assertEqual(posts.count(), 2)  # service message skip شد

        post1 = posts.filter(telegram_message_id=201).first()
        self.assertIsNotNone(post1)
        self.assertEqual(post1.content, "پیام اول از ZIP")
        self.assertEqual(post1.media_type, 'text')

        post2 = posts.filter(telegram_message_id=202).first()
        self.assertIsNotNone(post2)
        self.assertEqual(post2.content, "پیام **فرمت‌دار** از ZIP")

        # فایل ZIP موقت باید پاک شده باشد
        self.assertFalse(os.path.exists(filepath))

    # --- تست ۲: درون‌ریزی با مدیا (عکس) ---
    def test_zip_import_with_image_media(self):
        messages = [
            {
                "id": 301,
                "type": "message",
                "date": "2024-02-01T09:00:00",
                "text": "پیام با عکس",
                "photo": "photos/photo_1.jpg"
            },
        ]
        # ZIP با عکس fake
        extra_files = {"photos/photo_1.jpg": b"FAKE_JPEG_BINARY_DATA"}
        zip_bytes = self._make_zip_file(messages, extra_files=extra_files)
        task, filepath = self._create_task_and_write_zip(zip_bytes)

        process_telegram_zip_import(str(task.id), filepath)

        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')

        post = Post.objects.filter(topic=self.topic, telegram_message_id=301).first()
        self.assertIsNotNone(post)
        self.assertEqual(post.media_type, 'image')
        self.assertTrue(bool(post.media_file))  # فایل media_file ذخیره شده

    # --- تست ۳: ZIP بدون result.json → FAILED ---
    def test_zip_import_missing_result_json_fails(self):
        zip_bytes = self._make_zip_file([], include_result_json=False)
        task, filepath = self._create_task_and_write_zip(zip_bytes)

        process_telegram_zip_import(str(task.id), filepath)

        task.refresh_from_db()
        self.assertEqual(task.status, 'FAILED')
        self.assertIn('result.json', task.error_message)
        self.assertFalse(os.path.exists(filepath))

    # --- تست ۴: result.json خراب → FAILED ---
    def test_zip_import_corrupt_json_fails(self):
        zip_bytes = self._make_zip_file([], corrupt_json=True)
        task, filepath = self._create_task_and_write_zip(zip_bytes)

        process_telegram_zip_import(str(task.id), filepath)

        task.refresh_from_db()
        self.assertEqual(task.status, 'FAILED')
        self.assertFalse(os.path.exists(filepath))

    # --- تست ۵: ZIP خالی از پیام معتبر → COMPLETED با ۰ پست ---
    def test_zip_import_zero_valid_messages_completes(self):
        messages = [
            {"id": 401, "type": "service", "date": "2024-03-01T00:00:00", "text": "only service"},
        ]
        zip_bytes = self._make_zip_file(messages)
        task, filepath = self._create_task_and_write_zip(zip_bytes)

        process_telegram_zip_import(str(task.id), filepath)

        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')
        self.assertEqual(task.progress, 100)
        self.assertEqual(Post.objects.filter(topic=self.topic, is_imported=True).count(), 0)

    # --- تست ۶: جلوگیری از import مکرر (idempotency) ---
    def test_zip_import_skips_duplicate_telegram_ids(self):
        # پست اول از قبل موجود است
        Post.objects.create(
            topic=self.topic, author=self.user,
            content="پیام قدیمی", is_imported=True, telegram_message_id=501
        )
        messages = [
            {"id": 501, "type": "message", "date": "2024-04-01T00:00:00", "text": "تکراری"},
            {"id": 502, "type": "message", "date": "2024-04-01T00:01:00", "text": "جدید"},
        ]
        zip_bytes = self._make_zip_file(messages)
        task, filepath = self._create_task_and_write_zip(zip_bytes)

        process_telegram_zip_import(str(task.id), filepath)

        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')
        # فقط پست ۵۰۲ جدید اضافه شده، ۵۰۱ skip شده
        self.assertEqual(Post.objects.filter(topic=self.topic, is_imported=True).count(), 2)
        self.assertIsNone(Post.objects.filter(topic=self.topic, telegram_message_id=501).exclude(content="پیام قدیمی").first())

    # --- تست ۷: درون‌ریزی با مدیا و دایرکتوری والد (پوشه زیپ شده) ---
    def test_zip_import_with_parent_directory_and_media(self):
        messages = [
            {
                "id": 601,
                "type": "message",
                "date": "2024-05-01T09:00:00",
                "text": "پیام با دایرکتوری والد",
                "photo": "photos/photo_parent.jpg"
            },
        ]
        # شبیه‌سازی ساختار زیپ شده از یک پوشه اصلی (مثل ChatExport_...)
        parent = "ChatExport_2026-07-11"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            data = {"name": "Test Channel", "type": "public_channel", "messages": messages}
            zf.writestr(f"{parent}/result.json", json.dumps(data, ensure_ascii=False))
            zf.writestr(f"{parent}/photos/photo_parent.jpg", b"FAKE_JPEG_BINARY_DATA")
        buf.seek(0)
        zip_bytes = buf.read()
        
        task, filepath = self._create_task_and_write_zip(zip_bytes)
        process_telegram_zip_import(str(task.id), filepath)
        
        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')
        
        post = Post.objects.filter(topic=self.topic, telegram_message_id=601).first()
        self.assertIsNotNone(post)
        self.assertEqual(post.media_type, 'image')
        self.assertTrue(bool(post.media_file))


class TelegramImportEndpointRoutingTests(APITestCase):
    """تست‌های polymorphic routing endpoint import-json"""

    def setUp(self):
        self.user = User.objects.create_user(phone="09333333333", password="password")
        self.client.force_authenticate(user=self.user)
        self.topic = Topic.objects.create(name="تاپیک روتینگ", created_by=self.user)
        self.url = f"/api/notes/topics/{self.topic.id}/import-json/"

    def _make_minimal_zip(self):
        """کوچکترین ZIP معتبر حاوی result.json"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('result.json', json.dumps({"messages": []}))
        buf.seek(0)
        return buf.read()

    def _make_minimal_json(self):
        return json.dumps({"messages": []}).encode('utf-8')

    # --- تست ۷: ارسال ZIP → 202 و تسک با handler صحیح ---
    def test_endpoint_accepts_zip_file(self):
        zip_bytes = self._make_minimal_zip()
        uploaded = SimpleUploadedFile("export.zip", zip_bytes, content_type="application/zip")
        response = self.client.post(self.url, {"file": uploaded}, format="multipart")
        self.assertEqual(response.status_code, 202)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['status'], 'PENDING')

    # --- تست ۸: ارسال JSON → 202 (backward compatible) ---
    def test_endpoint_accepts_json_file_backward_compatible(self):
        json_bytes = self._make_minimal_json()
        uploaded = SimpleUploadedFile("result.json", json_bytes, content_type="application/json")
        response = self.client.post(self.url, {"file": uploaded}, format="multipart")
        self.assertEqual(response.status_code, 202)
        self.assertIn('id', response.data)

    # --- تست ۹: پسوند نامعتبر → 400 ---
    def test_endpoint_rejects_invalid_extension(self):
        uploaded = SimpleUploadedFile("export.txt", b"some content", content_type="text/plain")
        response = self.client.post(self.url, {"file": uploaded}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    # --- تست ۱۰: بدون فایل → 400 ---
    def test_endpoint_rejects_no_file(self):
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, 400)

    # --- تست ۱۱: غیر سازنده → 403 ---
    def test_endpoint_rejects_non_creator(self):
        other_user = User.objects.create_user(phone="09444444444")
        self.client.force_authenticate(user=other_user)
        zip_bytes = self._make_minimal_zip()
        uploaded = SimpleUploadedFile("export.zip", zip_bytes, content_type="application/zip")
        response = self.client.post(self.url, {"file": uploaded}, format="multipart")
        self.assertEqual(response.status_code, 403)

    # --- تست ۱۲: بدون احراز هویت → 401 یا 403 ---
    def test_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)
        zip_bytes = self._make_minimal_zip()
        uploaded = SimpleUploadedFile("export.zip", zip_bytes, content_type="application/zip")
        response = self.client.post(self.url, {"file": uploaded}, format="multipart")
        # DRF برمی‌گرداند 401 اگر WWW-Authenticate header وجود داشته باشد،
        # در غیر این صورت 403 — هر دو نشان‌دهنده عدم دسترسی هستند
        self.assertIn(response.status_code, [401, 403])


class FileCleanupSignalTests(APITestCase):
    """تست‌های بررسی حذف خودکار فایل‌های فیزیکی پس از حذف/تغییر رکوردها"""

    def setUp(self):
        self.user = User.objects.create_user(phone="09121234567", password="password")
        self.topic = Topic.objects.create(name="تاپیک تست سیگنال", created_by=self.user)
        
        # ساخت فایل‌های تستی فیزیکی
        from django.core.files.base import ContentFile
        
        self.topic_image_content = ContentFile(b"FAKE_IMAGE_DATA")
        self.topic.image.save("test_topic_image.jpg", self.topic_image_content, save=True)
        
        self.post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست تست سیگنال",
            media_type="image"
        )
        self.post_file_content = ContentFile(b"FAKE_POST_FILE_DATA")
        self.post.media_file.save("test_post_file.jpg", self.post_file_content, save=True)

    def test_delete_post_removes_physical_file(self):
        """تست اینکه با حذف پست، فایل فیزیکی آن نیز پاک می‌شود"""
        filepath = self.post.media_file.path
        self.assertTrue(os.path.exists(filepath))
        
        self.post.delete()
        self.assertFalse(os.path.exists(filepath))

    def test_delete_topic_removes_physical_image(self):
        """تست اینکه با حذف تاپیک، تصویر آن نیز پاک می‌شود"""
        image_path = self.topic.image.path
        self.assertTrue(os.path.exists(image_path))
        
        self.topic.delete()
        self.assertFalse(os.path.exists(image_path))

    def test_update_post_removes_old_physical_file(self):
        """تست اینکه با تغییر فایل پست، فایل قبلی پاک می‌شود"""
        old_filepath = self.post.media_file.path
        self.assertTrue(os.path.exists(old_filepath))
        
        # آپلود فایل جدید برای پست
        from django.core.files.base import ContentFile
        new_file_content = ContentFile(b"FAKE_NEW_POST_FILE_DATA")
        self.post.media_file.save("test_post_file_new.jpg", new_file_content, save=True)
        
        # بررسی اینکه فایل قدیمی حذف و فایل جدید موجود است
        self.assertFalse(os.path.exists(old_filepath))
        self.assertTrue(os.path.exists(self.post.media_file.path))

    def test_update_topic_removes_old_physical_image(self):
        """تست اینکه با تغییر تصویر تاپیک، تصویر قبلی پاک می‌شود"""
        old_image_path = self.topic.image.path
        self.assertTrue(os.path.exists(old_image_path))
        
        # آپلود تصویر جدید برای تاپیک
        from django.core.files.base import ContentFile
        new_image_content = ContentFile(b"FAKE_NEW_IMAGE_DATA")
        self.topic.image.save("test_topic_image_new.jpg", new_image_content, save=True)
        
        # بررسی اینکه تصویر قدیمی حذف و تصویر جدید موجود است
        self.assertFalse(os.path.exists(old_image_path))
        self.assertTrue(os.path.exists(self.topic.image.path))

    def test_cascade_delete_removes_post_physical_files(self):
        """تست اینکه با حذف تاپیک، تمامی فایل‌های پست‌های آن به صورت آبشاری پاک می‌شوند"""
        post_filepath = self.post.media_file.path
        topic_image_path = self.topic.image.path
        
        self.assertTrue(os.path.exists(post_filepath))
        self.assertTrue(os.path.exists(topic_image_path))
        
        self.topic.delete()
        
        self.assertFalse(os.path.exists(post_filepath))
        self.assertFalse(os.path.exists(topic_image_path))


from apps.notes.models import TopicAdmin


class TopicAdminTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(phone="09120000001", password="password")
        self.admin_user = User.objects.create_user(phone="09120000002", password="password")
        self.regular_user = User.objects.create_user(phone="09120000003", password="password")
        self.topic = Topic.objects.create(name="تاپیک مدیریت ادمین", created_by=self.owner)

    def test_topic_admin_model_and_str(self):
        admin_rec = TopicAdmin.objects.create(
            topic=self.topic,
            user=self.admin_user,
            promoted_by=self.owner,
            custom_title="مدیر بخش"
        )
        self.assertEqual(str(admin_rec), f"{self.admin_user.phone} - Admin of {self.topic.name}")

    def test_get_admins_endpoint_public(self):
        TopicAdmin.objects.create(topic=self.topic, user=self.admin_user, promoted_by=self.owner)
        url = f"/api/notes/topics/{self.topic.id}/admins/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['owner']['phone'], self.owner.phone)
        self.assertEqual(len(response.data['admins']), 1)
        self.assertEqual(response.data['admins'][0]['user']['phone'], self.admin_user.phone)

    def test_add_admin_by_owner_success(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/notes/topics/{self.topic.id}/add_admin/"
        response = self.client.post(url, {"user_id": self.admin_user.id, "custom_title": "Moderator"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TopicAdmin.objects.filter(topic=self.topic, user=self.admin_user).exists())

    def test_add_admin_by_non_owner_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        url = f"/api/notes/topics/{self.topic.id}/add_admin/"
        response = self.client.post(url, {"user_id": self.admin_user.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_owner_as_admin_bad_request(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/notes/topics/{self.topic.id}/add_admin/"
        response = self.client.post(url, {"user_id": self.owner.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_admin_by_owner_success(self):
        TopicAdmin.objects.create(topic=self.topic, user=self.admin_user, promoted_by=self.owner)
        self.client.force_authenticate(user=self.owner)
        url = f"/api/notes/topics/{self.topic.id}/remove_admin/{self.admin_user.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(TopicAdmin.objects.filter(topic=self.topic, user=self.admin_user).exists())

    def test_appointed_admin_can_create_post(self):
        TopicAdmin.objects.create(topic=self.topic, user=self.admin_user, promoted_by=self.owner)
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/notes/"
        response = self.client.post(url, {"topic": self.topic.id, "content": "پست توسط ادمین تاپیک"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_post_in_topic(self):
        self.client.force_authenticate(user=self.regular_user)
        url = "/api/notes/"
        response = self.client.post(url, {"topic": self.topic.id, "content": "پست غیرمجاز"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_transfer_ownership_by_owner_success(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/notes/topics/{self.topic.id}/transfer_ownership/"
        response = self.client.post(url, {"new_owner_id": self.admin_user.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.created_by, self.admin_user)
        # مالک قبلی باید تبدیل به ادمین شده باشد
        self.assertTrue(TopicAdmin.objects.filter(topic=self.topic, user=self.owner).exists())

    def test_transfer_ownership_by_non_owner_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        url = f"/api/notes/topics/{self.topic.id}/transfer_ownership/"
        response = self.client.post(url, {"new_owner_id": self.admin_user.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


from apps.notes.models import normalize_persian_text
from apps.notes.services import check_duplicate_message, execute_external_platform_deletion


class Phase2DeduplicationAndAsyncDeletionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09129998877", password="password")
        self.topic = Topic.objects.create(name="تاپیک فاز ۲", created_by=self.user)

    def test_persian_text_normalization(self):
        text1 = "سلام  علیكم\u200c دوست   عزیز"
        text2 = "سلام علیکم دوست عزیز"
        self.assertEqual(normalize_persian_text(text1), normalize_persian_text(text2))

    def test_content_hash_deduplication(self):
        post1 = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست تستی با  حروف  عربی علیكم"
        )
        self.assertIsNotNone(post1.content_hash)

        # Check duplicate using normalized text
        post_temp = Post(content="پست تستی با حروف عربی علیکم")
        is_dup, existing_post = check_duplicate_message(self.topic.id, post_temp.compute_content_hash())
        self.assertTrue(is_dup)
        self.assertEqual(existing_post, post1)

    def test_execute_external_platform_deletion(self):
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست برای حذف ناهمگام",
            telegram_message_ids={"chat_100": "999"},
            bale_message_ids={"chat_200": "888"},
            published_platforms=["telegram", "bale"]
        )

        execute_external_platform_deletion(
            post_id=post.id,
            delete_telegram=True,
            delete_bale=False,
            delete_database=False
        )

        post.refresh_from_db()
        # Telegram IDs cleared, Bale IDs untouched
        self.assertEqual(post.telegram_message_ids, {})
        self.assertEqual(post.bale_message_ids, {"chat_200": "888"})
        self.assertNotIn("telegram", post.published_platforms)
        self.assertIn("bale", post.published_platforms)

        # BotTask created for Telegram deletion
        task = BotTask.objects.filter(post_id=post, platform="telegram", action="delete").first()
        self.assertIsNotNone(task)
        self.assertEqual(task.chat_id, "chat_100")
        self.assertEqual(task.message_id, "999")


class Phase3ApiEndpointsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09127776655", password="password")
        self.client.force_authenticate(user=self.user)
        self.topic = Topic.objects.create(name="تاپیک فاز ۳", created_by=self.user)
        self.post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست برای تست اندپوینت‌ها",
            telegram_message_ids={"chat_123": "456"},
            published_platforms=["telegram"]
        )

    def test_check_duplicate_endpoint_found(self):
        url = "/api/notes/check-duplicate/"
        response = self.client.post(url, {
            "topic_id": self.topic.id,
            "content": "پست برای تست اندپوینت‌ها"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_duplicate"])
        self.assertEqual(response.data["existing_post_id"], self.post.id)

    def test_check_duplicate_endpoint_not_found(self):
        url = "/api/notes/check-duplicate/"
        response = self.client.post(url, {
            "topic_id": self.topic.id,
            "content": "متن غیرتکراری جدید"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_duplicate"])

    def test_selective_delete_endpoint_success(self):
        url = f"/api/notes/{self.post.id}/selective-delete/"
        response = self.client.post(url, {
            "delete_from_telegram": True,
            "delete_from_bale": False,
            "delete_from_db": False
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["message"], "Deletion request accepted.")

    def test_selective_delete_validation_error(self):
        url = f"/api/notes/{self.post.id}/selective-delete/"
        # Request deletion from Bale when post has no bale_message_ids
        response = self.client.post(url, {
            "delete_from_telegram": False,
            "delete_from_bale": True,
            "delete_from_db": False
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class TelegramBaleBotLifecycleTests(APITestCase):
    """
    تست‌های یکپارچه چرخه حیات ربات‌های بله و تلگرام:
    1. ارسال پست و صف‌بندی خودکار تسک‌های ربات (send)
    2. پردازش تسک‌ها توسط ربات و ثبت شناسه‌های پیام
    3. ویرایش پست و صف‌بندی خودکار تسک‌های ویرایش (edit)
    4. حذف انتخابی از یک پلتفرم (selective-delete)
    5. حذف کامل پست و صف‌بندی تسک‌های حذف (delete)
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone="09121112233"
        )
        self.user.telegram_bot_token = "111:FAKE_TG_TOKEN"
        self.user.bale_bot_token = "222:FAKE_BALE_TOKEN"
        self.user.save()
        self.client.force_authenticate(user=self.user)

        self.topic = Topic.objects.create(
            name="تاپیک همگام‌سازی بات‌ها",
            created_by=self.user,
            telegram_bot_active=True,
            bale_bot_active=True,
            post_badge="#کانال_تستی"
        )

        self.tg_target = MessagingTarget.objects.create(
            user=self.user,
            chat_id="tg_chat_1001",
            label="کانال تلگرام",
            platform="telegram",
            is_active=True
        )
        self.bale_target = MessagingTarget.objects.create(
            user=self.user,
            chat_id="bale_chat_2002",
            label="کانال بله",
            platform="bale",
            is_active=True
        )
        self.topic.telegram_connections.add(self.tg_target)
        self.topic.bale_connections.add(self.bale_target)

    def test_post_creation_dispatches_bot_tasks_for_both_platforms(self):
        """ارسال پست جدید باید تسک‌های ارسال جداگانه برای تلگرام و بله ایجاد کند"""
        url = "/api/notes/"
        response = self.client.post(url, {
            "topic": self.topic.id,
            "content": "متن تستی پست جدید"
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data["id"]
        post = Post.objects.get(id=post_id)

        # متن نهایی به دلیل وجود بج در تاپیک باید شامل امضا باشد
        self.assertIn("#کانال_تستی", post.content)

        # بررسی تسک‌های تلگرام و بله
        tg_task = BotTask.objects.filter(post_id=post, platform="telegram", action="send").first()
        bale_task = BotTask.objects.filter(post_id=post, platform="bale", action="send").first()

        self.assertIsNotNone(tg_task)
        self.assertEqual(tg_task.chat_id, "tg_chat_1001")
        self.assertEqual(tg_task.bot_token, "111:FAKE_TG_TOKEN")
        self.assertIn("متن تستی پست جدید", tg_task.text)

        self.assertIsNotNone(bale_task)
        self.assertEqual(bale_task.chat_id, "bale_chat_2002")
        self.assertEqual(bale_task.bot_token, "222:FAKE_BALE_TOKEN")
        self.assertIn("متن تستی پست جدید", bale_task.text)

    def test_bot_worker_processes_tasks_and_records_message_ids(self):
        """دریافت تسک‌ها و اعلام انجام کار توسط ورکر بات، شناسه‌های پیام را ذخیره می‌کند"""
        # ایجاد پست
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست برای تأیید ورکر"
        )
        tg_task = BotTask.objects.create(
            action="send",
            platform="telegram",
            chat_id="tg_chat_1001",
            text="پست برای تأیید ورکر",
            post_id=post,
            bot_token=self.user.telegram_bot_token
        )
        bale_task = BotTask.objects.create(
            action="send",
            platform="bale",
            chat_id="bale_chat_2002",
            text="پست برای تأیید ورکر",
            post_id=post,
            bot_token=self.user.bale_bot_token
        )

        # اعلام موفقیت ارسال تلگرام به اندپوینت bot_task_detail
        bot_key = getattr(settings, "BOT_API_KEY", "")
        bot_headers = {"HTTP_X_BOT_API_KEY": bot_key} if bot_key else {}

        detail_url_tg = f"/api/bot/tasks/{tg_task.id}/"
        resp_tg = self.client.post(detail_url_tg, {"message_id": "tg_msg_777"}, format="json", **bot_headers)
        self.assertEqual(resp_tg.status_code, status.HTTP_200_OK)

        # اعلام موفقیت ارسال بله به اندپوینت bot_task_detail
        detail_url_bale = f"/api/bot/tasks/{bale_task.id}/"
        resp_bale = self.client.post(detail_url_bale, {"message_id": "bale_msg_888"}, format="json", **bot_headers)
        self.assertEqual(resp_bale.status_code, status.HTTP_200_OK)

        # بررسی به‌روزرسانی پست
        post.refresh_from_db()
        self.assertEqual(post.telegram_message_ids.get("tg_chat_1001"), "tg_msg_777")
        self.assertEqual(post.bale_message_ids.get("bale_chat_2002"), "bale_msg_888")
        self.assertIn("telegram", post.published_platforms)
        self.assertIn("bale", post.published_platforms)

    def test_post_editing_dispatches_edit_bot_tasks(self):
        """ویرایش محتوای پست باید تسک‌های ویرایش (edit) را برای کانال‌های متصل بفرستد"""
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="متن اولیه قبل از ویرایش",
            telegram_message_ids={"tg_chat_1001": "tg_msg_777"},
            bale_message_ids={"bale_chat_2002": "bale_msg_888"},
            published_platforms=["telegram", "bale"]
        )

        edit_url = f"/api/notes/{post.id}/"
        response = self.client.patch(edit_url, {
            "content": "متن تغییریافته جدید"
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # بررسی صف وظایف: باید دو تسک ویرایش ایجاد شده باشد
        tg_edit_task = BotTask.objects.filter(post_id=post, platform="telegram", action="edit").first()
        bale_edit_task = BotTask.objects.filter(post_id=post, platform="bale", action="edit").first()

        self.assertIsNotNone(tg_edit_task)
        self.assertEqual(tg_edit_task.message_id, "tg_msg_777")
        self.assertEqual(tg_edit_task.chat_id, "tg_chat_1001")
        self.assertIn("متن تغییریافته جدید", tg_edit_task.text)

        self.assertIsNotNone(bale_edit_task)
        self.assertEqual(bale_edit_task.message_id, "bale_msg_888")
        self.assertEqual(bale_edit_task.chat_id, "bale_chat_2002")
        self.assertIn("متن تغییریافته جدید", bale_edit_task.text)

    @patch("threading.Thread")
    def test_selective_delete_telegram_only(self, mock_thread_cls):
        """حذف انتخابی از تلگرام فقط تسک حذف تلگرام می‌سازد و شناسه‌های بله دست‌نخورده می‌مانند"""
        mock_inst = MagicMock()
        mock_thread_cls.return_value = mock_inst

        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست ارسالی در هر دو پیام‌رسان",
            telegram_message_ids={"tg_chat_1001": "tg_msg_777"},
            bale_message_ids={"bale_chat_2002": "bale_msg_888"},
            published_platforms=["telegram", "bale"]
        )

        url = f"/api/notes/{post.id}/selective-delete/"
        response = self.client.post(url, {
            "delete_from_telegram": True,
            "delete_from_bale": False,
            "delete_from_db": False
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # اجرای عملیات پس‌زمینه به صورت همگام در همین تراکنش آزمایشی
        call_kwargs = mock_thread_cls.call_args[1]
        call_kwargs["target"](*call_kwargs["args"])

        post.refresh_from_db()
        self.assertEqual(post.telegram_message_ids, {})
        self.assertEqual(post.bale_message_ids, {"bale_chat_2002": "bale_msg_888"})
        self.assertNotIn("telegram", post.published_platforms)
        self.assertIn("bale", post.published_platforms)

        # بررسی ایجاد تسک حذف تلگرام
        delete_task = BotTask.objects.filter(post_id=post, platform="telegram", action="delete").first()
        self.assertIsNotNone(delete_task)
        self.assertEqual(delete_task.message_id, "tg_msg_777")

        # مطمئن شویم برای بله هیچ تسک حذفی ایجاد نشده است
        bale_delete_task = BotTask.objects.filter(post_id=post, platform="bale", action="delete").first()
        self.assertIsNone(bale_delete_task)

    def test_post_full_deletion_dispatches_delete_tasks(self):
        """حذف کامل پست باید تسک‌های حذف را برای تمام پیام‌رسان‌های فعال ایجاد کرده و پست را پاک کند"""
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست برای حذف کامل",
            telegram_message_ids={"tg_chat_1001": "tg_msg_777"},
            bale_message_ids={"bale_chat_2002": "bale_msg_888"},
            published_platforms=["telegram", "bale"]
        )
        post_id = post.id

        delete_url = f"/api/notes/{post_id}/"
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # پست از دیتابیس پاک شده است
        self.assertFalse(Post.objects.filter(id=post_id).exists())

        # تسک‌های حذف برای تلگرام و بله با شناسه پیام‌های صحیح ایجاد شده‌اند
        tg_del = BotTask.objects.filter(platform="telegram", action="delete", message_id="tg_msg_777").first()
        bale_del = BotTask.objects.filter(platform="bale", action="delete", message_id="bale_msg_888").first()

        self.assertIsNotNone(tg_del)
        self.assertEqual(tg_del.chat_id, "tg_chat_1001")

        self.assertIsNotNone(bale_del)
        self.assertEqual(bale_del.chat_id, "bale_chat_2002")

    def test_anonymous_comment_submission_unauthenticated(self):
        """ثبت نظر ناشناس توسط کاربر مهمان بدون لاگین"""
        self.client.force_authenticate(user=None)
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست برای کامنت ناشناس"
        )
        url = f"/api/notes/{post.id}/comments/"
        # بدون توکن احراز هویت
        response = self.client.post(
            url,
            {"content": "این یک نظر ناشناس عالی است!", "author_name": "سهراب"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_anonymous"])
        self.assertEqual(response.data["user_name"], "سهراب")
        self.assertIsNone(response.data["user_phone"])
        self.assertIsNone(response.data["user"])

        # بررسی در دیتابیس
        comment = PostComment.objects.get(id=response.data["id"])
        self.assertTrue(comment.is_anonymous)
        self.assertEqual(comment.author_name, "سهراب")
        self.assertIsNone(comment.user)

    def test_anonymous_comment_default_name(self):
        """ثبت نظر ناشناس بدون وارد کردن نام باید پیش‌فرض 'کاربر ناشناس' باشد"""
        self.client.force_authenticate(user=None)
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست برای کامنت ناشناس بدون نام"
        )
        url = f"/api/notes/{post.id}/comments/"
        response = self.client.post(
            url,
            {"content": "بدون نام ارسال شد"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user_name"], "کاربر ناشناس")
        self.assertTrue(response.data["is_anonymous"])
        self.assertIsNone(response.data["user_phone"])

    def test_anonymous_comment_authenticated_opt_in(self):
        """کاربر لاگین کرده می‌تواند با ارسال is_anonymous=True نظر ناشناس ثبت کند"""
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="پست برای کامنت کاربر لاگین کرده به صورت ناشناس"
        )
        url = f"/api/notes/{post.id}/comments/"
        response = self.client.post(
            url,
            {"content": "نظر از کاربر لاگین اما به صورت ناشناس", "is_anonymous": True, "author_name": "ناشناس محترم"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_anonymous"])
        self.assertEqual(response.data["user_name"], "ناشناس محترم")
        self.assertIsNone(response.data["user_phone"])

    def test_long_post_truncation_and_preview_link(self):
        """پست‌های طولانی‌تر از آستانه مجاز باید با لینک پیش‌نمایش به بات ارسال شوند"""
        from apps.notes.services import _post_markdown_text

        # متن بیش از ۱۰۰۰ کاراکتر
        long_content = "لورم ایپسوم " * 120
        post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content=long_content
        )

        formatted_tg = _post_markdown_text(post, platform="telegram")
        # باید حاوی لینک کوتاه به /p/{id} و متن راهنما باشد
        expected_link = f"/p/{post.id}"
        self.assertIn(expected_link, formatted_tg)
        self.assertIn("مشاهده و ثبت نظر در تفکر", formatted_tg)
        self.assertIn("...", formatted_tg)

    def test_post_link_mode_always_on_short_post(self):
        """در حالت always، حتی پست‌های کوتاه هم باید لینک و متن راهنما داشته باشند"""
        from apps.notes.services import _post_markdown_text

        self.topic.telegram_post_link_mode = 'always'
        self.topic.save()

        short_post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="یک پیام کوتاه تستی"
        )

        formatted_tg = _post_markdown_text(short_post, platform="telegram")
        expected_link = f"/p/{short_post.id}"
        self.assertIn(expected_link, formatted_tg)
        self.assertIn("مشاهده و ثبت نظر در تفکر", formatted_tg)
        self.assertIn("یک پیام کوتاه تستی", formatted_tg)

    def test_post_link_mode_auto_long_on_short_post(self):
        """در حالت auto_long، پست کوتاه نباید لینک داشته باشد"""
        from apps.notes.services import _post_markdown_text

        self.topic.telegram_post_link_mode = 'auto_long'
        self.topic.save()

        short_post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="یک پیام کوتاه تستی دیگر"
        )

        formatted_tg = _post_markdown_text(short_post, platform="telegram")
        expected_link = f"/p/{short_post.id}"
        self.assertNotIn(expected_link, formatted_tg)
        self.assertNotIn("مشاهده و ثبت نظر در تفکر", formatted_tg)
        self.assertIn("یک پیام کوتاه تستی دیگر", formatted_tg)

    def test_post_link_mode_disabled(self):
        """در حالت disabled، لینک حتی برای پست‌های طولانی درج نمی‌شود"""
        from apps.notes.services import _post_markdown_text

        self.topic.telegram_post_link_mode = 'disabled'
        self.topic.save()

        long_post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="متن بلند " * 150
        )

        formatted_tg = _post_markdown_text(long_post, platform="telegram")
        expected_link = f"/p/{long_post.id}"
        self.assertNotIn(expected_link, formatted_tg)
        self.assertNotIn("مشاهده و ثبت نظر در تفکر", formatted_tg)


class TopicFAQTests(APITestCase):
    """تست‌های جامع مدل، سطوح دسترسی و اندپوینت‌های TopicFAQ"""

    def setUp(self):
        self.owner = User.objects.create_user(phone="09121111111", password="password")
        self.admin_user = User.objects.create_user(phone="09122222222", password="password")
        self.regular_user = User.objects.create_user(phone="09123333333", password="password")

        self.topic = Topic.objects.create(name="تاپیک پرسش و پاسخ", created_by=self.owner)
        TopicAdmin.objects.create(topic=self.topic, user=self.admin_user, custom_title="مدیر کمکی")

        # ایجاد چند سوال تستی
        self.faq1 = TopicFAQ.objects.create(
            topic=self.topic,
            question="هدف از ایجاد این تاپیک چیست؟",
            answer="این تاپیک برای پاسخ به سوالات اساسی ایجاد شده است.",
            order=1,
            is_published=True,
            created_by=self.owner
        )
        self.faq2 = TopicFAQ.objects.create(
            topic=self.topic,
            question="قوانین گفتگو چگونه است؟",
            answer="رعایت احترام به اعضا الزامی است.",
            order=2,
            is_published=True,
            created_by=self.owner
        )
        self.faq_draft = TopicFAQ.objects.create(
            topic=self.topic,
            question="پیش‌نویس سوال هنوز منتشر نشده",
            answer="پاسخ پیش‌نویس",
            order=3,
            is_published=False,
            created_by=self.owner
        )

    def test_public_can_view_only_published_faqs(self):
        """کاربر عادی و مهمان تنها سوالات منتشر شده را می‌بینند"""
        url = f"/api/notes/topics/{self.topic.id}/faqs/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # فقط ۲ سوال منتشر شده باید برگردد
        self.assertEqual(len(response.data), 2)
        questions = [item['question'] for item in response.data]
        self.assertIn("هدف از ایجاد این تاپیک چیست؟", questions)
        self.assertNotIn("پیش‌نویس سوال هنوز منتشر نشده", questions)

    def test_owner_can_view_all_faqs_including_drafts(self):
        """مالک تاپیک پیش‌نویس‌ها را نیز می‌بیند"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/notes/topics/{self.topic.id}/faqs/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_owner_can_create_faq(self):
        """سازنده تاپیک می‌تواند سوال جدید اضافه کند"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/notes/topics/{self.topic.id}/faqs/"
        payload = {
            "question": "آیا شرکت در جلسات رایگان است؟",
            "answer": "بله تمامی جلسات عمومی رایگان هستند.",
            "order": 4
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["question"], payload["question"])
        self.assertTrue(TopicFAQ.objects.filter(question=payload["question"]).exists())

    def test_topic_admin_can_create_faq(self):
        """ادمین تاپیک مجاز به ثبت سوال جدید است"""
        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/notes/topics/{self.topic.id}/faqs/"
        payload = {
            "question": "سوال ثبت شده توسط ادمین",
            "answer": "پاسخ از طرف ادمین",
            "order": 5
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_faq(self):
        """کاربر غریبه و غیرادمین اجازه ثبت سوال رسمی ندارد (403)"""
        self.client.force_authenticate(user=self.regular_user)
        url = f"/api/notes/topics/{self.topic.id}/faqs/"
        payload = {
            "question": "تلاش برای ثبت سوال توسط کاربر عادی",
            "answer": "پاسخ نامعتبر",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_update_and_delete_faq(self):
        """ویرایش و حذف سوال توسط مالک تاپیک"""
        self.client.force_authenticate(user=self.owner)
        
        # ویرایش
        edit_url = f"/api/notes/faqs/{self.faq1.id}/"
        response = self.client.patch(edit_url, {"question": "عنوان ویرایش شده سوال"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.faq1.refresh_from_db()
        self.assertEqual(self.faq1.question, "عنوان ویرایش شده سوال")

        # حذف
        del_url = f"/api/notes/faqs/{self.faq2.id}/"
        del_response = self.client.delete(del_url)
        self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TopicFAQ.objects.filter(id=self.faq2.id).exists())

    def test_faq_reordering(self):
        """تغییر چیدمان و ترتیب سوالات توسط مالک تاپیک"""
        self.client.force_authenticate(user=self.owner)
        reorder_url = "/api/notes/faqs/reorder/"
        payload = {
            "topic_id": self.topic.id,
            "orders": [
                {"id": self.faq1.id, "order": 10},
                {"id": self.faq2.id, "order": 1}
            ]
        }
        response = self.client.post(reorder_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.faq1.refresh_from_db()
        self.faq2.refresh_from_db()
        self.assertEqual(self.faq1.order, 10)
        self.assertEqual(self.faq2.order, 1)

    def test_faq_search_filter(self):
        """فیلتر سرچ سوالات بر اساس کلمات کلیدی"""
        url = f"/api/notes/topics/{self.topic.id}/faqs/?search=قوانین"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.faq2.id)


from apps.notes.models import TopicChatSession, TopicChatMessage


class TopicAIChatTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="09121111111", password="password")
        self.topic = Topic.objects.create(name="هوش مصنوعی و یادگیری ماشین", description="مباحث تخصصی یادگیری عمیق")
        
        # ثبت FAQ
        self.faq = TopicFAQ.objects.create(
            topic=self.topic,
            question="پیش‌نیاز یادگیری ماشین چیست؟",
            answer="جبر خطی، حساب دیفرانسیل و پایتون مقدماتی.",
            is_published=True
        )

        # ثبت چند پست
        self.post1 = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="کتابخانه PyTorch بهترین گزینه برای توسعه مدل‌های یادگیری عمیق و ترنسفورمرها است."
        )
        self.post2 = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content="جلسه بررسی شبکه‌های کانولوشنی این هفته دوشنبه ساعت ۱۸ برگزار می‌شود."
        )

    def test_ai_chat_creates_session_and_messages(self):
        """تست اینکه ارسال پیام به اندپوینت چت، سشن و پیام‌های کاربر و هوش مصنوعی را می‌سازد"""
        url = f"/api/notes/topics/{self.topic.id}/chat/"
        payload = {"message": "پیش‌نیاز این تاپیک چیه؟"}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("session_id", response.data)
        self.assertIn("user_message", response.data)
        self.assertIn("assistant_message", response.data)

        # بررسی در دیتابیس
        session_id = response.data["session_id"]
        session = TopicChatSession.objects.get(id=session_id)
        self.assertEqual(session.topic, self.topic)
        self.assertEqual(session.messages.count(), 2)
        
        user_msg = session.messages.filter(role="user").first()
        assistant_msg = session.messages.filter(role="assistant").first()
        self.assertEqual(user_msg.content, "پیش‌نیاز این تاپیک چیه؟")
        self.assertTrue(len(assistant_msg.content) > 0)
        self.assertTrue(len(assistant_msg.sources) > 0)

    def test_ai_chat_session_continuation(self):
        """تست ادامه گفت‌وگو در یک سشن مشخص"""
        url = f"/api/notes/topics/{self.topic.id}/chat/"
        res1 = self.client.post(url, {"message": "سلام"}, format="json")
        session_id = res1.data["session_id"]

        res2 = self.client.post(url, {"message": "درباره PyTorch توضیح بده", "session_id": session_id}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["session_id"], session_id)

        session = TopicChatSession.objects.get(id=session_id)
        self.assertEqual(session.messages.count(), 4)

    def test_ai_chat_history_retrieval(self):
        """تست دریافت تاریخچه پیام‌های سشن"""
        url = f"/api/notes/topics/{self.topic.id}/chat/"
        res = self.client.post(url, {"message": "جلسه کی برگزار میشه؟"}, format="json")
        session_id = res.data["session_id"]

        hist_url = f"/api/notes/topics/{self.topic.id}/chat-history/?session_id={session_id}"
        hist_res = self.client.get(hist_url)
        self.assertEqual(hist_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(hist_res.data["messages"]), 2)

    def test_ai_chat_clear(self):
        """تست پاکسازی تاریخچه گفت‌وگو"""
        url = f"/api/notes/topics/{self.topic.id}/chat/"
        res = self.client.post(url, {"message": "پیام برای پاک شدن"}, format="json")
        session_id = res.data["session_id"]

        clear_url = f"/api/notes/topics/{self.topic.id}/chat-clear/"
        clear_res = self.client.post(clear_url, {"session_id": session_id}, format="json")
        self.assertEqual(clear_res.status_code, status.HTTP_200_OK)
        self.assertFalse(TopicChatSession.objects.filter(id=session_id).exists())

    def test_ai_chat_topic_isolation(self):
        """تست عدم تداخل اطلاعات و ارجاعات بین دو تاپیک متفاوت"""
        other_topic = Topic.objects.create(name="تاپیک آشپزی و شیرینی‌پزی")
        Post.objects.create(topic=other_topic, author=self.user, content="دستور پخت کیک هویج")

        url = f"/api/notes/topics/{self.topic.id}/chat/"
        res = self.client.post(url, {"message": "کیک هویج"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # ارجاعات نباید پست تاپیک آشپزی را داشته باشد
        sources = res.data["assistant_message"]["sources"]
        for s in sources:
            if s.get("type") == "post":
                post_obj = Post.objects.get(id=s["id"])
                self.assertEqual(post_obj.topic, self.topic)






