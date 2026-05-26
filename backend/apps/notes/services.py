# apps/notes/services.py
from __future__ import annotations

import json
from typing import Optional

from apps.accounts.models import MessagingTarget

from .models import BotTask, Note


def get_chat_ids_for_platform(note: Note, platform: str) -> list[str]:
    """تعیین لیست تمام chat_idهای فعال برای ارسال پیام: کانال یادداشت → مقاصد فعال → چت شخصی."""
    if note.channel:
        channel_chat_id = getattr(note.channel, f"{platform}_chat_id", None)
        if channel_chat_id:
            return [str(channel_chat_id)]

    targets = MessagingTarget.objects.filter(
        user=note.user,
        platform=platform,
        is_active=True,
    )
    if targets.exists():
        return [str(t.chat_id) for t in targets]

    personal = getattr(note.user, f"{platform}_chat_id", None)
    return [str(personal)] if personal else []


def get_message_ids(note: Note, platform: str) -> dict[str, str]:
    """دریافت شناسه‌های پیام به صورت دیکشنری {chat_id: message_id}"""
    val = getattr(note, f"{platform}_message_id", None)
    if not val:
        return {}
    try:
        data = json.loads(val)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {"default": str(val)}


def set_message_ids(note: Note, platform: str, message_ids: dict[str, str]):
    """ذخیره شناسه‌های پیام"""
    field = f"{platform}_message_id"
    val = json.dumps(message_ids) if message_ids else None
    setattr(note, field, val)
    Note.objects.filter(id=note.id).update(**{field: val})


def _note_markdown_text(note: Note) -> str:
    """متن ارسالی به ربات؛ عنوان به‌صورت ساده تا کاراکترهای خاص Markdown خرابش نکند."""
    if note.title:
        return f"{note.title}\n\n{note.content}"
    return note.content


def create_bot_tasks(note: Note, old_instance: Optional[Note] = None, *, is_delete: bool = False):
    """
    صف وظایف ربات را برای یادداشت می‌سازد.
    old_instance: وضعیت قبلی هنگام به‌روزرسانی؛ برای ایجاد تازه None است.
    is_delete: True یعنی کاربر در حال حذف یادداشت است (فقط تسک حذف پیام).
    """
    if is_delete:
        for platform in ("telegram", "bale"):
            msg_ids = get_message_ids(note, platform)
            bot_token = note.user.telegram_bot_token if platform == "telegram" else note.user.bale_bot_token
            for chat_id, msg_id in msg_ids.items():
                actual_chat_id = chat_id
                if actual_chat_id == "default":
                    ch_ids = get_chat_ids_for_platform(note, platform)
                    actual_chat_id = ch_ids[0] if ch_ids else None
                if msg_id and actual_chat_id:
                    BotTask.objects.create(
                        action="delete",
                        platform=platform,
                        chat_id=str(actual_chat_id),
                        text="",
                        message_id=str(msg_id),
                        note_id=note.id,
                        bot_token=bot_token,
                    )
        return

    for platform in ("telegram", "bale"):
        send_field = f"send_to_{platform}"
        old_send = getattr(old_instance, send_field, False) if old_instance else False
        new_send = getattr(note, send_field)
        bot_token = note.user.telegram_bot_token if platform == "telegram" else note.user.bale_bot_token

        if old_instance is None:
            if new_send:
                chat_ids = get_chat_ids_for_platform(note, platform)
                for chat_id in chat_ids:
                    BotTask.objects.create(
                        action="send",
                        platform=platform,
                        chat_id=str(chat_id),
                        text=_note_markdown_text(note),
                        message_id=None,
                        note_id=note.id,
                        bot_token=bot_token,
                    )
            continue

        if old_send and not new_send:
            msg_ids = get_message_ids(old_instance, platform)
            for chat_id, msg_id in msg_ids.items():
                actual_chat_id = chat_id
                if actual_chat_id == "default":
                    ch_ids = get_chat_ids_for_platform(note, platform)
                    actual_chat_id = ch_ids[0] if ch_ids else None
                if msg_id and actual_chat_id:
                    BotTask.objects.create(
                        action="delete",
                        platform=platform,
                        chat_id=str(actual_chat_id),
                        text="",
                        message_id=str(msg_id),
                        note_id=note.id,
                        bot_token=bot_token,
                    )
        elif not old_send and new_send:
            chat_ids = get_chat_ids_for_platform(note, platform)
            for chat_id in chat_ids:
                BotTask.objects.create(
                    action="send",
                    platform=platform,
                    chat_id=str(chat_id),
                    text=_note_markdown_text(note),
                    message_id=None,
                    note_id=note.id,
                    bot_token=bot_token,
                )
        elif old_send and new_send:
            msg_ids = get_message_ids(old_instance, platform)
            current_active_chat_ids = get_chat_ids_for_platform(note, platform)
            content_changed = (old_instance.title != note.title or old_instance.content != note.content)

            # ۱. ویرایش پیام‌های ارسالی قبلی
            for chat_id, msg_id in msg_ids.items():
                actual_chat_id = chat_id
                if actual_chat_id == "default":
                    ch_ids = get_chat_ids_for_platform(note, platform)
                    actual_chat_id = ch_ids[0] if ch_ids else None
                if msg_id and actual_chat_id:
                    if content_changed:
                        BotTask.objects.create(
                            action="edit",
                            platform=platform,
                            chat_id=str(actual_chat_id),
                            text=_note_markdown_text(note),
                            message_id=str(msg_id),
                            note_id=note.id,
                            bot_token=bot_token,
                        )

            # ۲. ارسال به کانال‌های جدید فعال که قبلاً ارسال نشده بودند
            for chat_id in current_active_chat_ids:
                if chat_id not in msg_ids:
                    BotTask.objects.create(
                        action="send",
                        platform=platform,
                        chat_id=str(chat_id),
                        text=_note_markdown_text(note),
                        message_id=None,
                        note_id=note.id,
                        bot_token=bot_token,
                    )

