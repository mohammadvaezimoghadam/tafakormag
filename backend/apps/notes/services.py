# apps/notes/services.py
from __future__ import annotations

import json
import logging
import os
import traceback
from typing import Optional
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_aware, now as tz_now

from apps.accounts.models import MessagingTarget
from .models import BotTask, Post, ImportTask

logger = logging.getLogger("notes.services")


def get_message_ids(post: Post, platform: str) -> dict[str, str]:
    """دریافت شناسه‌های پیام به صورت دیکشنری {chat_id: message_id}"""
    if platform == "telegram":
        return post.telegram_message_ids or {}
    elif platform == "bale":
        return post.bale_message_ids or {}
    return {}


def set_message_ids(post: Post, platform: str, message_ids: dict[str, str]):
    """ذخیره شناسه‌های پیام"""
    if platform == "telegram":
        post.telegram_message_ids = message_ids
        Post.objects.filter(id=post.id).update(telegram_message_ids=message_ids)
    elif platform == "bale":
        post.bale_message_ids = message_ids
        Post.objects.filter(id=post.id).update(bale_message_ids=message_ids)


def _post_markdown_text(post: Post) -> str:
    """متن ارسالی به ربات"""
    return post.content


def create_bot_tasks(post: Post, old_instance: Optional[Post] = None, *, is_delete: bool = False):
    """
    صف وظایف ربات را برای پست ایجاد می‌کند.
    old_instance: وضعیت قبلی هنگام به‌روزرسانی؛ برای ایجاد تازه None است.
    is_delete: True یعنی کاربر در حال حذف پست است.
    """
    if getattr(post, 'is_imported', False):
        return

    if is_delete:
        for platform in ("telegram", "bale"):
            msg_ids = get_message_ids(post, platform)
            bot_token = post.author.telegram_bot_token if platform == "telegram" else post.author.bale_bot_token
            
            for chat_id, msg_id in msg_ids.items():
                if msg_id and chat_id:
                    BotTask.objects.create(
                        action="delete",
                        platform=platform,
                        chat_id=str(chat_id),
                        text="",
                        message_id=str(msg_id),
                        note_id=post.id, # سازگاری با سیستم‌های قدیمی
                        post_id=post,
                        bot_token=bot_token,
                    )
        return

    # برای ایجاد یا ویرایش پست
    for platform in ("telegram", "bale"):
        active_field = f"{platform}_bot_active"
        is_bot_active = getattr(post.topic, active_field, False)
        
        bot_token = post.author.telegram_bot_token if platform == "telegram" else post.author.bale_bot_token
        
        # اگر ربات فعال نباشد یا توکن نداشته باشیم، کاری انجام نمی‌دهیم
        if not is_bot_active or not bot_token:
            continue

        # دریافت اهداف ارتباط متصل به این تاپیک
        connections_field = f"{platform}_connections"
        connections = getattr(post.topic, connections_field).filter(is_active=True)
        chat_ids = [str(conn.chat_id) for conn in connections]

        if old_instance is None:
            # ۱. پست جدید: ارسال به تمام کانال‌های متصل
            for chat_id in chat_ids:
                BotTask.objects.create(
                    action="send",
                    platform=platform,
                    chat_id=str(chat_id),
                    text=_post_markdown_text(post),
                    message_id=None,
                    note_id=post.id,
                    post_id=post,
                    bot_token=bot_token,
                )
        else:
            # ۲. ویرایش پست
            msg_ids = get_message_ids(old_instance, platform)
            content_changed = (old_instance.content != post.content or 
                               old_instance.media_type != post.media_type or 
                               old_instance.media_file != post.media_file)

            # الف) ویرایش در کانال‌هایی که قبلاً ارسال شده است
            for chat_id, msg_id in msg_ids.items():
                if msg_id and chat_id in chat_ids:
                    if content_changed:
                        BotTask.objects.create(
                            action="edit",
                            platform=platform,
                            chat_id=str(chat_id),
                            text=_post_markdown_text(post),
                            message_id=str(msg_id),
                            note_id=post.id,
                            post_id=post,
                            bot_token=bot_token,
                        )
                elif msg_id and chat_id not in chat_ids:
                    # اگر از لیست اتصالات حذف شده است، پیام قبلی را حذف کنیم
                    BotTask.objects.create(
                        action="delete",
                        platform=platform,
                        chat_id=str(chat_id),
                        text="",
                        message_id=str(msg_id),
                        note_id=post.id,
                        post_id=post,
                        bot_token=bot_token,
                    )

            # ب) ارسال به کانال‌های جدیدی که به اتصالات اضافه شده‌اند ولی هنوز ارسال نشده بودند
            for chat_id in chat_ids:
                if chat_id not in msg_ids:
                    BotTask.objects.create(
                        action="send",
                        platform=platform,
                        chat_id=str(chat_id),
                        text=_post_markdown_text(post),
                        message_id=None,
                        note_id=post.id,
                        post_id=post,
                        bot_token=bot_token,
                    )


def process_telegram_json_import(task_id: str, temp_filepath: str):
    """
    یک کار پیش‌زمینه غیرمسدودکننده برای درون‌ریزی پیام‌های فایل JSON خروجی تلگرام.
    فایل موقت آپلود شده در نهایت در بلاک finally حذف می‌شود.
    """
    logger.info(f"Starting Telegram JSON import process for Task ID: {task_id}")
    task = None
    try:
        # 1. بازیابی تسک
        task = ImportTask.objects.filter(id=task_id).first()
        if not task:
            logger.error(f"ImportTask with ID {task_id} not found.")
            return

        # تنظیم وضعیت به استخراج
        task.status = 'EXTRACTING'
        task.current_stage = 'در حال خواندن و استخراج پیام‌ها...'
        task.progress = 10
        task.save()

        # 2. بررسی وجود فایل و بارگذاری محتوای فایل JSON
        if not os.path.exists(temp_filepath):
            raise FileNotFoundError(f"فایل موقت یافت نشد: {temp_filepath}")

        with open(temp_filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"فایل آپلود شده یک فایل JSON معتبر نیست: {str(e)}")

        # قالب خروجی تلگرام معمولاً دارای کلید messages است
        if not isinstance(data, dict) or 'messages' not in data:
            raise ValueError("ساختار فایل تلگرام معتبر نیست. کلید 'messages' یافت نشد.")

        raw_messages = data['messages']
        if not isinstance(raw_messages, list):
            raise ValueError("لیست پیام‌ها ('messages') باید یک آرایه باشد.")

        total_messages = len(raw_messages)
        logger.info(f"Total raw messages extracted: {total_messages}")

        # فیلتر پیام‌ها (فقط پیام‌های عادی با متن و شناسه)
        # تلگرام فیلد type="message" را برای پیام‌های عادی دارد
        valid_raw_messages = []
        for msg in raw_messages:
            if not isinstance(msg, dict):
                continue
            # فقط پیام‌های عادی را ایمپورت کنیم (از پیام‌های خدماتی مثل دعوت، تغییر عکس و غیره بگذریم)
            if msg.get('type') != 'message':
                continue
            # چک کردن شناسه و تاریخ
            if 'id' not in msg or 'date' not in msg:
                continue
            valid_raw_messages.append(msg)

        total_valid = len(valid_raw_messages)
        logger.info(f"Total valid messages to import: {total_valid}")

        if total_valid == 0:
            task.status = 'COMPLETED'
            task.current_stage = 'هیچ پیامی برای درون‌ریزی یافت نشد.'
            task.progress = 100
            task.save()
            return

        # تغییر وضعیت به درون‌ریزی
        task.status = 'IMPORTING'
        task.current_stage = 'در حال ثبت پیام‌ها در دیتابیس...'
        task.progress = 30
        task.save()

        # 3. پردازش پیام‌ها و ایجاد شیء پست
        posts_to_create = []
        author = task.topic.created_by
        if not author:
            # اگر سازنده‌ای نباشد، از اولین سوپریوزر یا ادمین استفاده کنیم
            from apps.accounts.models import User
            author = User.objects.filter(is_superuser=True).first()
            if not author:
                author = User.objects.first()

        # خواندن تک‌تک پیام‌ها و تبدیل به Post
        for index, msg in enumerate(valid_raw_messages):
            msg_id = msg['id']
            raw_date = msg['date'] # "2023-05-15T12:30:45" or similar ISO
            
            # تبدیل تاریخ به datetime آگاه از منطقه زمانی (Timezone-aware)
            dt = parse_datetime(raw_date)
            if not dt:
                # تلاش برای پارس مستقیم
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(raw_date)
                except Exception:
                    dt = tz_now()

            if dt and not is_aware(dt):
                dt = make_aware(dt)

            # تبدیل متن پیام تلگرام
            text_content = ""
            text_entities = msg.get('text', '')
            # تلگرام گاهی متن را به صورت لیستی از اشیاء متنی (برای فرمت‌ها مثل لینک، بولد و غیره) یا متن ساده می‌دهد
            if isinstance(text_entities, list):
                # تبدیل آرایه پیام تلگرام به متن ساده یا مارک‌داون ساده
                parts = []
                for part in text_entities:
                    if isinstance(part, dict):
                        part_text = part.get('text', '')
                        part_type = part.get('type', '')
                        if part_type == 'link':
                            parts.append(f"[{part_text}]({part.get('href', part_text)})")
                        elif part_type == 'bold':
                            parts.append(f"**{part_text}**")
                        elif part_type == 'italic':
                            parts.append(f"*{part_text}*")
                        elif part_type == 'code':
                            parts.append(f"`{part_text}`")
                        else:
                            parts.append(part_text)
                    else:
                        parts.append(str(part))
                text_content = "".join(parts)
            else:
                text_content = str(text_entities)

            # نادیده گرفتن پیام‌های خالی
            if not text_content.strip():
                continue

            post = Post(
                topic=task.topic,
                author=author,
                content=text_content,
                media_type='text',
                is_imported=True,
                telegram_message_id=int(msg_id)
            )
            # مقداردهی دستی created_at در صورت پارس معتبر
            if dt:
                post.created_at = dt
            posts_to_create.append(post)

        # 4. نوشتن دسته‌ای در دیتابیس با bulk_create
        total_posts = len(posts_to_create)
        logger.info(f"Total posts mapped for database creation: {total_posts}")

        batch_size = 500
        for i in range(0, total_posts, batch_size):
            chunk = posts_to_create[i:i + batch_size]
            
            # استفاده از bulk_create
            Post.objects.bulk_create(chunk)
            
            # به روز رسانی پیشرفت به صورت پویا
            chunk_progress = 30 + int((min(i + batch_size, total_posts) / total_posts) * 65)
            task.progress = min(95, chunk_progress)
            task.current_stage = f"در حال درون‌ریزی پیام‌ها ({min(i + batch_size, total_posts)} از {total_posts})..."
            task.save()

        # آپدیت فیلد توضیحات تاپیک (Topic Description) بر اساس آخرین پیام
        try:
            # درون‌ریزی داینامیک برای جلوگیری از مشکلات چرخه وارداتی (circular imports)
            from .views import update_topic_description
            update_topic_description(task.topic)
        except Exception as e:
            logger.warning(f"Failed to update topic description: {str(e)}")

        # تکمیل تسک
        task.status = 'COMPLETED'
        task.current_stage = 'درون‌ریزی تاریخچه تلگرام با موفقیت به پایان رسید.'
        task.progress = 100
        task.save()
        logger.info(f"Import process COMPLETED successfully for Task ID: {task_id}")

    except Exception as e:
        logger.error(f"Error processing Telegram import for Task: {task_id}. Error: {str(e)}")
        logger.error(traceback.format_exc())
        if task:
            task.status = 'FAILED'
            task.current_stage = 'خطا در اجرای فرآیند درون‌ریزی.'
            task.error_message = f"{str(e)}\n\n{traceback.format_exc()}"
            task.progress = 100
            task.save()
    finally:
        # پاکسازی فایل موقت برای جلوگیری از پر شدن دیسک
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                logger.info(f"Cleaned up temp import file: {temp_filepath}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_filepath}: {str(e)}")
