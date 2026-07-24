from django.test import TestCase
from django.db import IntegrityError
from apps.accounts.models import User, MessagingTarget
from apps.notes.models import Topic, Post, PostReaction, PostComment, BotTask, ImportTask


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




