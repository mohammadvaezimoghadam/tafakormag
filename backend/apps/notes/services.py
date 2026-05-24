# apps/notes/services.py
from __future__ import annotations

from typing import Optional

from apps.accounts.models import MessagingTarget

from .models import BotTask, Note


def get_chat_id_for_platform(note: Note, platform: str) -> Optional[str]:
    """تعیین chat_id برای ارسال پیام: کانال یادداشت → مقصد پیش‌فرض → چت شخصی."""
    if note.channel:
        channel_chat_id = getattr(note.channel, f"{platform}_chat_id", None)
        if channel_chat_id:
            return str(channel_chat_id)

    target = MessagingTarget.objects.filter(
        user=note.user,
        platform=platform,
        is_default=True,
    ).first()
    if target:
        return target.chat_id

    target = MessagingTarget.objects.filter(
        user=note.user,
        platform=platform,
    ).first()
    if target:
        return target.chat_id

    personal = getattr(note.user, f"{platform}_chat_id", None)
    return str(personal) if personal else None


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
            msg_id = getattr(note, f"{platform}_message_id")
            chat_id = get_chat_id_for_platform(note, platform)
            if msg_id and chat_id:
                bot_token = note.user.telegram_bot_token if platform == "telegram" else note.user.bale_bot_token
                BotTask.objects.create(
                    action="delete",
                    platform=platform,
                    chat_id=str(chat_id),
                    text="",
                    message_id=str(msg_id),
                    note_id=note.id,
                    bot_token=bot_token,
                )
        return

    for platform in ("telegram", "bale"):
        chat_id = get_chat_id_for_platform(note, platform)
        if not chat_id:
            continue

        send_field = f"send_to_{platform}"
        msg_field = f"{platform}_message_id"

        old_send = getattr(old_instance, send_field, False) if old_instance else False
        new_send = getattr(note, send_field)
        old_msg_id = getattr(old_instance, msg_field, None) if old_instance else None
        bot_token = note.user.telegram_bot_token if platform == "telegram" else note.user.bale_bot_token

        if old_instance is None:
            if new_send:
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

        if old_send and not new_send and old_msg_id:
            BotTask.objects.create(
                action="delete",
                platform=platform,
                chat_id=str(chat_id),
                text="",
                message_id=str(old_msg_id),
                note_id=note.id,
                bot_token=bot_token,
            )
        elif not old_send and new_send:
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
            if old_msg_id:
                if old_instance.title != note.title or old_instance.content != note.content:
                    BotTask.objects.create(
                        action="edit",
                        platform=platform,
                        chat_id=str(chat_id),
                        text=_note_markdown_text(note),
                        message_id=str(old_msg_id),
                        note_id=note.id,
                        bot_token=bot_token,
                    )
            else:
                BotTask.objects.create(
                    action="send",
                    platform=platform,
                    chat_id=str(chat_id),
                    text=_note_markdown_text(note),
                    message_id=None,
                    note_id=note.id,
                    bot_token=bot_token,
                )
