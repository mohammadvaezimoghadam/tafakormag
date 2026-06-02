# apps/notes/services.py
from __future__ import annotations

import json
import logging
from typing import Optional

from apps.accounts.models import MessagingTarget
from .models import BotTask, Post

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
