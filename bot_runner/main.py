import os
import asyncio
import httpx
import logging
import html
import re
import time
from urllib.parse import urlparse, urlunparse
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ChatMemberHandler
)
from telegram.error import TelegramError

from api_client import APIClient
from logger_config import setup_logger

def format_text_for_telegram(text: str) -> str:
    if not text:
        return ""
    # 1. Escape HTML special characters
    escaped = html.escape(text)
    
    # 2. Convert standard markdown sequences to HTML:
    # inline code: `code` -> <code>code</code>
    escaped = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', escaped)
    # bold: **bold** -> <b>bold</b>
    escaped = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', escaped)
    # italic: *italic* -> <i>italic</i>
    escaped = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', escaped)
    
    return escaped

# تنظیم لاگر
logger = setup_logger("bot_runner", "runner.log")
api_client = APIClient()

TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "https://api.telegram.org/bot").strip()
BALE_API_URL = "https://tapi.bale.ai/bot"

# لیست کلاینت‌های در حال اجرای ربات‌های شخصی کاربران
# ساختار: { "platform_user_id": (task, app_instance) }
running_bots = {}
rate_limit_delays = {}

# ---------- Handlers ربات‌های اختصاصی کاربران ----------

def get_custom_main_keyboard():
    keyboard = [
        [KeyboardButton("📋 لیست مقاصد (کانال‌ها/گروه‌ها)")],
        [KeyboardButton("➕ راهنمای اتصال مقصد"), KeyboardButton("🔌 وضعیت اتصال به تفکر")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def custom_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.bot_data.get("phone", "نامشخص")
    chat_id = update.effective_chat.id
    platform = context.bot_data.get("platform")
    
    if platform and phone != "نامشخص" and update.effective_chat.type == "private":
        try:
            await api_client.register_phone_chat(platform, phone, chat_id)
            context.bot_data["owner_chat_id"] = chat_id
            logger.info(f"Automatically registered chat_id {chat_id} for owner {phone} ({platform}) via custom_start")
        except Exception as e:
            logger.error(f"Failed to auto-register owner chat_id: {e}")

    await update.message.reply_text(
        f"🧠 <b>به ربات اختصاصی تفکر خوش آمدید!</b>\n\n"
        f"این ربات به صورت اختصاصی به حساب تفکر شما با شماره <code>{format_text_for_telegram(phone)}</code> متصل است.\n\n"
        f"💡 <b>راه‌های اتصال مقصد جدید (گروه یا کانال):</b>\n\n"
        f"1️⃣ <b>اتصال خودکار:</b> ربات را به عنوان مدیر (Admin) با دسترسی ارسال پیام به کانال یا گروه خود اضافه کنید تا بلافاصله به صورت خودکار متصل شود.\n\n"
        f"2️⃣ <b>اتصال با شناسه (دستی):</b> شناسه عددی (Chat ID) گروه یا کانال خود را مستقیماً در این چت ارسال کنید. (مثلاً: <code>-100123456789</code>).\n\n"
        f"💡 <b>نکته برای گروه‌های از قبل عضو شده:</b>\n"
        f"اگر ربات از قبل در گروه یا کانال شما عضو بوده است، کافیست شناسه عددی آن را در همین چت خصوصی ارسال کنید تا متصل شود.\n\n"
        f"🔹 برای مشاهده و مدیریت لیست مقاصد متصل، از دکمه زیر صفحه استفاده کنید:",
        parse_mode="HTML",
        reply_markup=get_custom_main_keyboard()
    )

async def custom_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.bot_data.get("phone", "نامشخص")
    await update.message.reply_text(
        f"🔌 <b>وضعیت اتصال به تفکر:</b>\n\n"
        f"این ربات اختصاصی با موفقیت به حساب تفکر با شماره <code>{format_text_for_telegram(phone)}</code> متصل است و آماده انتشار یادداشت‌های شما می‌باشد.",
        parse_mode="HTML",
        reply_markup=get_custom_main_keyboard()
    )

async def custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>راهنمای اتصال مقاصد انتشار</b>\n\n"
        "برای اینکه یادداشت‌های شما در کانال یا گروه منتشر شوند، باید آن‌ها را متصل کنید:\n\n"
        "🔹 <b>نحوه اتصال خودکار کانال/گروه:</b>\n"
        "۱. ربات را به گروه یا کانال خود دعوت کنید.\n"
        "۲. ربات را مدیر (Admin) با دسترسی ارسال پیام کنید.\n"
        "۳. ربات به طور خودکار آن را شناسایی، ثبت و پیام تایید برای شما ارسال می‌کند.\n\n"
        "🔹 <b>نحوه اتصال با شناسه چت (مستقیم):</b>\n"
        "اگر شناسه عددی چت خود را دارید (معمولاً شناسه کانال‌ها با <code>-100</code> شروع می‌شود)، آن را مستقیماً به همین چت ارسال کنید تا ثبت شود.\n\n"
        "🔹 <b>مدیریت مقاصد:</b>\n"
        "از دکمه «📋 لیست مقاصد (کانال‌ها/گروه‌ها)» برای مشاهده مقاصد متصل استفاده کنید.",
        parse_mode="HTML",
        reply_markup=get_custom_main_keyboard()
    )

async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت خودکار مقصد بدون نیاز به دستور (Zero-Command Member Event)"""
    my_chat_member = update.my_chat_member
    if not my_chat_member:
        return

    chat = my_chat_member.chat
    chat_id = str(chat.id)
    new_status = my_chat_member.new_chat_member.status
    
    # اگر ربات از کانال/گروه لفت داد یا کیک شد
    if new_status in ("left", "kicked"):
        user_id = context.bot_data.get("user_id")
        platform = context.bot_data.get("platform")
        owner_chat_id = context.bot_data.get("owner_chat_id")
        try:
            res = await api_client.unregister_chat(platform, chat_id)
            if res and res.get("success"):
                if "known_destinations" in context.bot_data:
                    context.bot_data["known_destinations"].discard(chat_id)
                notifications = res.get("notifications", [])
                
                # منطق پشتیبان در صورت خالی بودن اعلان‌ها از دیتابیس
                if not notifications and owner_chat_id:
                    notifications.append({
                        "chat_id": owner_chat_id,
                        "label": chat.title or "گروه/کانال",
                        "chat_id_removed": chat_id
                    })
                
                for notif in notifications:
                    if not notif.get("chat_id"):
                        continue
                    try:
                        await context.bot.send_message(
                            chat_id=int(notif["chat_id"]),
                            text=(
                                f"⚠️ <b>قطع اتصال مقصد انتشار {'تلگرام' if platform == 'telegram' else 'بله'}</b>\n\n"
                                f"ربات تفکر از مقصد «{format_text_for_telegram(notif['label'])}» (با شناسه <code>{notif['chat_id_removed']}</code>) خارج شد.\n"
                                f"این مقصد با موفقیت از سیستم تفکر شما حذف گردید."
                            ),
                            parse_mode="HTML"
                        )
                    except Exception as notify_err:
                        logger.error(f"Error sending custom bot unregister notification to {notif['chat_id']}: {notify_err}")
                logger.info(f"Unregistered {platform} chat {chat_id} due to bot status: {new_status}")
        except Exception as e:
            logger.error(f"Failed to unregister {platform} chat {chat_id}: {e}")
        return

    # در صورتی که ربات به عنوان ادمین یا عضو اضافه شده باشد
    if new_status in ("administrator", "member"):
        user_id = context.bot_data.get("user_id")
        platform = context.bot_data.get("platform")
        phone = context.bot_data.get("phone")
        owner_chat_id = context.bot_data.get("owner_chat_id")
        label = chat.title or f"Chat {chat_id}"
        
        logger.info(f"Auto-registering chat {chat_id} ({label}) for user {user_id} ({platform})")
        try:
            # فراخوانی وب‌سرویس ثبت مقصد به صورت مستقیم
            await api_client.register_destination(user_id, platform, chat_id, label)
            if "known_destinations" in context.bot_data:
                context.bot_data["known_destinations"].add(chat_id)
            
            target_chat_id = owner_chat_id or (my_chat_member.from_user.id if my_chat_member.from_user else None)
            if target_chat_id:
                # ارسال پیام خصوصی تایید به صاحب ربات
                await context.bot.send_message(
                    chat_id=int(target_chat_id),
                    text=(
                        f"✅ <b>ثبت خودکار مقصد موفقیت‌آمیز بود!</b>\n\n"
                        f"📢 نام مقصد: <code>{format_text_for_telegram(label)}</code>\n"
                        f"🆔 شناسه: <code>{chat_id}</code>\n\n"
                        f"این چت با موفقیت به مقاصد انتشار حساب تفکر شما (<code>{format_text_for_telegram(phone)}</code>) اضافه شد."
                    ),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Auto-registration failed: {e}")

async def on_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر کمکی برای عضویت ربات اختصاصی در گروه‌ها"""
    message = update.message
    if not message or not message.new_chat_members:
        return

    chat = message.chat
    chat_id = str(chat.id)
    
    # بررسی اینکه آیا خود ربات به گروه اضافه شده است
    bot_added = any(member.id == context.bot.id for member in message.new_chat_members)
    if not bot_added:
        return

    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    phone = context.bot_data.get("phone")
    owner_chat_id = context.bot_data.get("owner_chat_id")
    
    logger.info(f"Custom bot added to group {chat_id} ({chat.title}) for user {user_id}")
    try:
        if platform == "bale":
            is_admin = True
        else:
            chat_member = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
            is_admin = chat_member.status in ("administrator", "creator")
        
        if is_admin:
            label = chat.title or f"Chat {chat_id}"
            await api_client.register_destination(user_id, platform, chat_id, label)
            if "known_destinations" in context.bot_data:
                context.bot_data["known_destinations"].add(chat_id)
            
            target_chat_id = owner_chat_id or (message.from_user.id if message.from_user else None)
            if target_chat_id:
                await context.bot.send_message(
                    chat_id=int(target_chat_id),
                    text=(
                        f"✅ <b>اتصال خودکار گروه موفقیت‌آمیز بود!</b>\n\n"
                        f"📢 نام گروه: <code>{format_text_for_telegram(label)}</code>\n"
                        f"🆔 شناسه: <code>{chat_id}</code>\n\n"
                        f"این گروه با موفقیت به مقاصد انتشار حساب تفکر شما متصل شد."
                    ),
                    parse_mode="HTML"
                )
        else:
            target_chat_id = owner_chat_id or (message.from_user.id if message.from_user else None)
            if target_chat_id:
                await context.bot.send_message(
                    chat_id=int(target_chat_id),
                    text=(
                        f"💡 شما ربات تفکر را به گروه «{format_text_for_telegram(chat.title)}» اضافه کردید.\n\n"
                        f"برای فعال‌سازی کامل و ارسال خودکار یادداشت‌ها، لطفاً ربات را در این گروه **مدیر (Admin)** کنید تا اتصال برقرار شود."
                    ),
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Auto-registration in on_new_chat_members failed: {e}")

async def on_left_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر کمکی برای خروج/حذف ربات اختصاصی از گروه‌ها"""
    message = update.message
    if not message or not message.left_chat_member:
        return

    chat = message.chat
    chat_id = str(chat.id)
    
    # بررسی اینکه آیا خود ربات خارج/حذف شده است
    if message.left_chat_member.id != context.bot.id:
        return

    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    owner_chat_id = context.bot_data.get("owner_chat_id")
    
    logger.info(f"Custom bot left/removed from group {chat_id} ({chat.title}) for user {user_id}")
    try:
        res = await api_client.unregister_chat(platform, chat_id)
        if res and res.get("success"):
            if "known_destinations" in context.bot_data:
                context.bot_data["known_destinations"].discard(chat_id)
            target_chat_id = owner_chat_id or (message.from_user.id if message.from_user else None)
            if target_chat_id:
                try:
                    await context.bot.send_message(
                        chat_id=int(target_chat_id),
                        text=(
                            f"⚠️ <b>قطع اتصال مقصد انتشار {'تلگرام' if platform == 'telegram' else 'بله'}</b>\n\n"
                            f"ربات تفکر از مقصد «{format_text_for_telegram(chat.title or 'گروه')}» (با شناسه <code>{chat_id}</code>) خارج شد.\n"
                            f"این مقصد با موفقیت از سیستم تفکر شما حذف گردید."
                        ),
                        parse_mode="HTML"
                    )
                except Exception as notify_err:
                    logger.error(f"Error sending custom bot unregister notification on left_chat_member: {notify_err}")
    except Exception as e:
        logger.error(f"Failed to unregister chat on left_chat_member: {e}")

async def send_destinations_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مقاصد متصل با قابلیت فعال/غیرفعال‌سازی و حذف کامل"""
    chat = update.effective_chat
    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    
    destinations = await api_client.get_destinations(user_id, platform)
    
    valid_destinations = []
    for dest in destinations:
        chat_id = dest["chat_id"]
        try:
            if platform == "bale":
                # Skip get_chat_member check for Bale to prevent permission_denied false negatives
                valid_destinations.append(dest)
            else:
                await context.bot.get_chat_member(chat_id=int(chat_id), user_id=context.bot.id)
                valid_destinations.append(dest)
        except Exception as e:
            # ربات از گروه/کانال خارج شده یا دسترسی ندارد
            logger.info(f"Automatically unregistering unreachable destination {chat_id} for user {user_id} due to get_chat_member error: {e}")
            try:
                owner_chat_id = context.bot_data.get("owner_chat_id")
                if owner_chat_id:
                    try:
                        await context.bot.send_message(
                            chat_id=int(owner_chat_id),
                            text=(
                                f"⚠️ <b>قطع اتصال مقصد انتشار {'تلگرام' if platform == 'telegram' else 'بله'}</b>\n\n"
                                f"ربات تفکر از مقصد «{format_text_for_telegram(dest.get('label', 'گروه/کانال'))}» (با شناسه <code>{chat_id}</code>) خارج شد.\n"
                                f"این مقصد با موفقیت از سیستم تفکر شما حذف گردید."
                            ),
                            parse_mode="HTML"
                        )
                    except Exception as notify_err:
                        logger.error(f"Error sending kick message: {notify_err}")

                await api_client.unregister_chat(platform, chat_id)
                if "known_destinations" in context.bot_data:
                    context.bot_data["known_destinations"].discard(chat_id)
            except Exception as unreg_err:
                logger.error(f"Failed to auto-unregister chat {chat_id} in list: {unreg_err}")

    if not valid_destinations:
        await update.effective_message.reply_text(
            "📭 در حال حاضر هیچ گروه یا کانالی متصل نشده است.\n\n"
            "برای اضافه کردن مقصد جدید، دکمه «➕ راهنمای اتصال مقصد» را کلیک کنید یا شناسه چت را بفرستید."
        )
        return

    await update.effective_message.reply_text(
        "📋 <b>لیست مقاصد متصل شده به تفکر:</b>",
        parse_mode="HTML"
    )
    
    for dest in valid_destinations:
        label = dest["label"]
        chat_id = dest["chat_id"]
        
        text = (
            f"📢 <b>نام:</b> {format_text_for_telegram(label)}\n"
            f"🆔 <b>شناسه:</b> <code>{chat_id}</code>\n\n"
            f"💡 <b>راهنمای لغو اتصال:</b> برای قطع اتصال این مقصد، کافیست ربات تفکر را از این گروه/کانال ریمو (حذف) کنید. سیستم تفکر به صورت خودکار اتصال را قطع و از لیست حذف خواهد کرد."
        )
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            parse_mode="HTML"
        )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    
    if data.startswith("toggle_"):
        dest_id = int(data.split("_")[1])
        result = await api_client.toggle_active_destination(user_id, platform, dest_id)
        if result and result.get("success"):
            is_active = result.get("is_active", False)
            status_text = "🟢 فعال" if is_active else "🔴 غیرفعال"
            
            orig_text = query.message.text
            lines = orig_text.split("\n")
            new_lines = []
            for line in lines:
                if "📊 وضعیت:" in line or "وضعیت:" in line:
                    new_lines.append(f"📊 وضعیت: {status_text}")
                else:
                    new_lines.append(line)
            new_text = "\n".join(new_lines)
            
            buttons = []
            if is_active:
                buttons.append(InlineKeyboardButton("🔴 غیرفعال‌سازی", callback_data=f"toggle_{dest_id}"))
            else:
                buttons.append(InlineKeyboardButton("🟢 فعال‌سازی", callback_data=f"toggle_{dest_id}"))
            buttons.append(InlineKeyboardButton("❌ حذف", callback_data=f"delete_{dest_id}"))
            
            reply_markup = InlineKeyboardMarkup([buttons])
            try:
                await query.edit_message_text(
                    text=new_text,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to edit message in callback: {e}")
        else:
            await query.answer("❌ خطا در تغییر وضعیت مقصد.", show_alert=True)
            
    elif data.startswith("delete_"):
        dest_id = int(data.split("_")[1])
        success = await api_client.delete_destination(user_id, platform, dest_id)
        if success:
            await query.edit_message_text(
                text=query.message.text + "\n\n❌ این مقصد با موفقیت حذف شد."
            )
        else:
            await query.answer("❌ خطا در حذف مقصد.", show_alert=True)

    elif data.startswith("retry_"):
        try:
            task_id = int(data.split("_")[1])
            success = await api_client.retry_task(task_id)
            if success:
                await query.answer("🔄 یادداشت مجدداً در صف انتشار قرار گرفت.", show_alert=True)
            else:
                await query.answer("❌ خطا در تلاش مجدد.", show_alert=True)
        except Exception as e:
            await query.answer("❌ مشکلی پیش آمد، دوباره تلاش کنید.", show_alert=True)
            logger.error(f"button_callback retry error: {e}")

    elif data.startswith("view_"):
        try:
            task_id = int(data.split("_")[1])
            task_details = await api_client.get_task_details(task_id)
            if task_details and task_details.get("text"):
                note_text = task_details.get("text")
                chat_id = query.message.chat_id if query.message else query.from_user.id
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"📋 <b>متن یادداشت:</b>\n\n{note_text}",
                    parse_mode="HTML"
                )
                await query.answer("📋 متن یادداشت ارسال شد.")
            else:
                await query.answer("❌ متن یادداشت یافت نشد.", show_alert=True)
        except Exception as e:
            await query.answer("❌ مشکلی پیش آمد، دوباره تلاش کنید.", show_alert=True)
            logger.error(f"button_callback view error: {e}")

async def handle_any_message_or_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message:
        return

    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    phone = context.bot_data.get("phone", "نامشخص")

    # ۳. بررسی و اتصال خودکار پس از ارتقا به ادمین (مخصوصاً برای بله که رویداد تغییر وضعیت ادمین ندارد)
    if chat.type in ("group", "supergroup", "channel"):
        chat_id = str(chat.id)
        if "known_destinations" not in context.bot_data:
            try:
                dests = await api_client.get_destinations(user_id, platform)
                context.bot_data["known_destinations"] = {str(d["chat_id"]) for d in dests}
            except Exception as load_err:
                logger.error(f"Failed to load destinations in fallback check: {load_err}")
                context.bot_data["known_destinations"] = set()
        
        known_dests = context.bot_data["known_destinations"]
        if chat_id not in known_dests:
            try:
                if platform == "bale":
                    is_admin = True
                else:
                    chat_member = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
                    is_admin = chat_member.status in ("administrator", "creator")
                if is_admin:
                    label = chat.title or f"Chat {chat_id}"
                    await api_client.register_destination(user_id, platform, chat_id, label)
                    known_dests.add(chat_id)
                    logger.info(f"Auto-registered chat {chat_id} via fallback check for user {user_id}")
                    
                    owner_chat_id = context.bot_data.get("owner_chat_id")
                    target_chat_id = owner_chat_id or (message.from_user.id if message.from_user else None)
                    if target_chat_id:
                        await context.bot.send_message(
                            chat_id=int(target_chat_id),
                            text=(
                                f"✅ <b>ثبت خودکار مقصد موفقیت‌آمیز بود!</b>\n\n"
                                f"📢 نام مقصد: <code>{format_text_for_telegram(label)}</code>\n"
                                f"🆔 شناسه: <code>{chat_id}</code>\n\n"
                                f"این چت با موفقیت به مقاصد انتشار حساب تفکر شما (<code>{format_text_for_telegram(phone)}</code>) اضافه شد."
                            ),
                            parse_mode="HTML"
                        )
            except Exception as auto_reg_err:
                logger.warning(f"Auto-registration fallback check failed for chat {chat_id}: {auto_reg_err}")

    # برای بقیه دستورات و پیام‌های خصوصی نیاز به متن پیام داریم
    # اما اگر پیام از یک کانال/گروه فوروارد شده باشد، می‌توانیم آن را مستقیماً ثبت کنیم
    fwd_chat = getattr(message, "forward_from_chat", None)
    if chat.type == "private" and fwd_chat:
        if fwd_chat.type in ("channel", "group", "supergroup"):
            fwd_chat_id = str(fwd_chat.id)
            label = fwd_chat.title or fwd_chat.username or fwd_chat.first_name or fwd_chat_id
            logger.info(f"Attempting registration via forwarded message for chat: {fwd_chat_id} ({label})")
            try:
                await api_client.register_destination(user_id, platform, fwd_chat_id, label)
                await message.reply_text(
                    f"✅ <b>ثبت مقصد با موفقیت انجام شد!</b>\n\n"
                    f"📢 نام مقصد: <code>{format_text_for_telegram(label)}</code>\n"
                    f"🆔 شناسه: <code>{fwd_chat_id}</code>\n\n"
                    f"این مقصد از طریق پیام فوروارد شده با موفقیت به مقاصد انتشار حساب شما اضافه شد.",
                    parse_mode="HTML"
                )
            except Exception as e:
                await message.reply_text(
                    f"❌ خطا در ثبت مقصد فوروارد شده.\n\n"
                    f"مطمئن شوید ربات را در آن کانال/گروه عضو کرده و دسترسی مدیریت (Admin) به آن داده‌اید.\n\n"
                    f"جزئیات خطا: {e}"
                )
            return

    if not message.text:
        return

    text = message.text.strip()

    # ۱. اگر دستور ثبت در گروه یا کانال باشد
    if text.startswith(("/connect", "/register", "/start")) and chat.type in ("group", "supergroup", "channel"):
        chat_id = str(chat.id)
        label = chat.title or f"Chat {chat_id}"
        logger.info(f"Registering chat via command {text}: {chat_id} ({label})")
        try:
            await api_client.register_destination(user_id, platform, chat_id, label)
            await message.reply_text(
                f"✅ <b>ثبت مقصد موفقیت‌آمیز بود!</b>\n\n"
                f"📢 نام مقصد: <code>{format_text_for_telegram(label)}</code>\n"
                f"🆔 شناسه: <code>{chat_id}</code>\n\n"
                f"این چت با موفقیت به مقاصد انتشار حساب تفکر شما (<code>{format_text_for_telegram(phone)}</code>) اضافه شد.",
                parse_mode="HTML"
            )
        except Exception as e:
            await message.reply_text(f"⚠️ ثبت مقصد انجام نشد یا قبلاً ثبت شده است.\nشناسه چت: `{chat_id}`\nجزئیات: {e}")
        return

    # ۲. مدیریت چت خصوصی ربات
    if chat.type == "private":
        if platform and phone != "نامشخص":
            try:
                await api_client.register_phone_chat(platform, phone, chat.id)
            except Exception as e:
                logger.error(f"Failed to auto-register owner chat_id in handle_any_message_or_post: {e}")

        # الف) منوی نمایش مقاصد
        if text in ("📋 لیست مقاصد (کانال‌ها/گروه‌ها)", "/destinations", "/list"):
            await send_destinations_list(update, context)
            return

        # ب) منوی راهنمای اتصال مقصد
        if text in ("➕ راهنمای اتصال مقصد", "/help"):
            await custom_help(update, context)
            return

        # ج) دکمه وضعیت اتصال به تفکر
        if text in ("🔌 وضعیت اتصال به تفکر", "/status"):
            await custom_status(update, context)
            return

        # د) وارد کردن شناسه عددی یا نام کاربری چت برای ثبت مستقیم
        is_username = text.startswith('@') and len(text) > 1
        clean_text = text.lstrip('-')
        if clean_text.isdigit() or is_username:
            chat_id = text
            logger.info(f"Attempting manual chat registration for: {chat_id}")
            try:
                chat_obj = await context.bot.get_chat(chat_id if is_username else int(chat_id))
                resolved_chat_id = str(chat_obj.id)
                label = chat_obj.title or chat_obj.username or f"Chat {resolved_chat_id}"
                await api_client.register_destination(user_id, platform, resolved_chat_id, label)
                await message.reply_text(
                    f"✅ <b>ثبت مقصد با موفقیت انجام شد!</b>\n\n"
                    f"📢 نام مقصد: <code>{format_text_for_telegram(label)}</code>\n"
                    f"🆔 شناسه: <code>{resolved_chat_id}</code>\n\n"
                    f"این چت به مقاصد انتشار حساب شما اضافه شد.",
                    parse_mode="HTML"
                )
            except Exception as e:
                target_str = "نام کاربری" if is_username else "شناسه"
                await message.reply_text(
                    f"❌ خطا در دسترسی به چت با {target_str} {chat_id}.\n\n"
                    f"مطمئن شوید:\n"
                    f"۱. {target_str} را درست وارد کرده‌اید (شناسه عددی کانال‌ها معمولاً با -100 شروع می‌شود).\n"
                    f"۲. ربات را در آن کانال/گروه عضو کرده و دسترسی مدیریت (Admin) به آن داده‌اید.\n\n"
                    f"جزئیات خطا: {e}"
                )
            return

        # ه) پیام متنی متفرقه در چت خصوصی
        await custom_start(update, context)

async def custom_bot_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    logger.error(f"Error in custom bot: {error}")
    
    from telegram.error import Conflict, InvalidToken
    is_conflict = isinstance(error, Conflict) or "conflict" in str(error).lower()
    is_unauthorized = isinstance(error, InvalidToken) or "unauthorized" in str(error).lower() or "invalid token" in str(error).lower()
    
    if is_conflict or is_unauthorized:
        user_id = context.bot_data.get("user_id")
        platform = context.bot_data.get("platform")
        reason = "conflict" if is_conflict else "unauthorized"
        logger.warning(f"Disconnect condition ({reason}) detected for custom bot (user_id={user_id}, platform={platform}). Shutting down...")
        if user_id and platform:
            try:
                await api_client.report_bot_disconnect(user_id, platform, reason)
            except Exception as e:
                logger.error(f"Failed to report bot disconnect to backend: {e}")
        
        if context.application and context.application.updater.running:
            asyncio.create_task(context.application.updater.stop())
            asyncio.create_task(context.application.stop())

# ---------- مدیریت داینامیک کلاینت‌های ربات‌ها ----------

async def run_single_bot(bot_key: str, token: str, platform: str, user_id: int, phone: str, owner_chat_id: int = None):
    """راه‌اندازی کلاینت مستقل ربات با کتابخانه python-telegram-bot"""
    logger.info(f"Starting custom bot task for user {user_id} ({platform}) with owner_chat_id={owner_chat_id}")
    
    builder = ApplicationBuilder().token(token)
    if platform == "telegram":
        if TELEGRAM_API_URL and TELEGRAM_API_URL != "https://api.telegram.org/bot":
            builder.base_url(TELEGRAM_API_URL)
    else:
        builder.base_url(BALE_API_URL)
        builder.base_file_url(f"{BALE_API_URL}/file")

    app = builder.build()
    
    # تزریق داده‌های کاربر به حافظه ربات
    app.bot_data["user_id"] = user_id
    app.bot_data["phone"] = phone
    app.bot_data["platform"] = platform
    app.bot_data["owner_chat_id"] = owner_chat_id

    # هندلرهای ربات اختصاصی
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_chat_members))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_chat_member))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL | filters.ALL, handle_any_message_or_post))
    
    app.add_error_handler(custom_bot_error_handler)

    try:
        async with app:
            await app.start()
            
            # ارسال پیام خوش‌آمدگویی استارت‌آپ به مالک ربات در صورت مشخص بودن شناسه چت
            if owner_chat_id:
                try:
                    await app.bot.send_message(
                        chat_id=int(owner_chat_id),
                        text=(
                            f"🧠 <b>ربات اختصاصی تفکر شما با موفقیت متصل شد!</b>\n\n"
                            f"این ربات آماده مدیریت و ارسال یادداشت‌های شما می‌باشد.\n\n"
                            f"💡 <b>راهنمای اتصال مقصد جدید:</b>\n"
                            f"کافیست ربات را به کانال یا گروه خود اضافه کرده و آن را مدیر (Admin) با دسترسی ارسال پیام کنید تا اتصال به صورت کاملاً خودکار برقرار شود.\n\n"
                            f"🔹 برای مشاهده لیست مقاصد خود از دکمه «📋 لیست مقاصد (کانال‌ها/گروه‌ها)» استفاده کنید."
                        ),
                        parse_mode="HTML",
                        reply_markup=get_custom_main_keyboard()
                    )
                except Exception as startup_err:
                    logger.warning(f"Could not send startup message to owner {owner_chat_id}: {startup_err}")

            poll_interval = 2.0 if platform == "bale" else 0.0
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, poll_interval=poll_interval)
            await asyncio.Event().wait()
    except Exception as e:
        from telegram.error import Conflict, InvalidToken
        is_conflict = isinstance(e, Conflict) or "conflict" in str(e).lower()
        is_unauthorized = isinstance(e, InvalidToken) or "unauthorized" in str(e).lower() or "invalid token" in str(e).lower()
        if is_conflict or is_unauthorized:
            reason = "conflict" if is_conflict else "unauthorized"
            logger.warning(f"Startup disconnect condition ({reason}) detected for bot {bot_key}: {e}")
            try:
                await api_client.report_bot_disconnect(user_id, platform, reason)
            except Exception as report_err:
                logger.error(f"Failed to report startup bot disconnect ({reason}) to backend: {report_err}")
        else:
            logger.error(f"Error running bot {bot_key}: {e}")
    finally:
        logger.info(f"Stopping bot {bot_key}")
        await app.updater.stop()
        await app.stop()

async def dynamic_bot_manager():
    """مدیریت، خاموش/روشن کردن و مانیتورینگ ربات‌های اختصاصی کاربران"""
    logger.info("Dynamic Bot Manager loop started")
    while True:
        try:
            # 1. دریافت بات‌های فعال
            active_bots = await api_client.get_active_custom_bots()
            active_keys = set()
            for bot in active_bots:
                uid = bot["user_id"]
                platform = bot["platform"]
                bot_key = f"{platform}_{uid}"
                active_keys.add(bot_key)

            # 2. متوقف کردن و شات‌دان تسک‌های ربات‌هایی که دیگر فعال نیستند
            tasks_to_await = []
            for bot_key in list(running_bots.keys()):
                if bot_key not in active_keys:
                    logger.info(f"Bot {bot_key} is no longer active, terminating task...")
                    task = running_bots.pop(bot_key)
                    task.cancel()
                    tasks_to_await.append(task)
            
            if tasks_to_await:
                # صبر می‌کنیم تا کاملاً متوقف شوند تا پورت/اتصالات آزاد شوند
                await asyncio.gather(*tasks_to_await, return_exceptions=True)
                logger.info("All inactive bot tasks terminated successfully.")

            # 3. پاکسازی تسک‌های خاتمه یافته قبلی (که ممکن است کرش کرده باشند)
            for bot_key, task in list(running_bots.items()):
                if task.done():
                    try:
                        exc = task.exception()
                        if exc:
                            logger.error(f"Bot task {bot_key} failed: {exc}")
                    except Exception:
                        pass
                    running_bots.pop(bot_key)
                    logger.info(f"Removed inactive/failed bot task: {bot_key}")

            # 4. راه‌اندازی ربات‌های فعال جدید
            for bot in active_bots:
                uid = bot["user_id"]
                platform = bot["platform"]
                token = bot["token"].strip()
                phone = bot["phone"]
                owner_chat_id = bot.get("owner_chat_id")
                bot_key = f"{platform}_{uid}"
                
                # اگر ربات در حال اجرا نیست، آن را استارت بزن
                if bot_key not in running_bots:
                    logger.info(f"New active bot detected: {bot_key}, launching...")
                    task = asyncio.create_task(run_single_bot(bot_key, token, platform, uid, phone, owner_chat_id))
                    running_bots[bot_key] = task
                    
        except Exception as e:
            logger.error(f"Error in dynamic_bot_manager: {e}")
            
        await asyncio.sleep(20)

def get_internal_media_url(media_url: str) -> str:
    if not media_url:
        return ""
    try:
        parsed = urlparse(media_url)
        # Reconstruct url using the internal docker host and port for backend service
        new_netloc = "backend:8000"
        return urlunparse((parsed.scheme, new_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    except Exception as e:
        logger.error(f"Error parsing media url {media_url}: {e}")
        return media_url

async def download_file(http_client: httpx.AsyncClient, url: str) -> bytes | None:
    try:
        res = await http_client.get(url)
        if res.status_code == 200:
            return res.content
        else:
            logger.error(f"Failed to download file from {url}: status={res.status_code}")
    except Exception as e:
        logger.error(f"Exception downloading file from {url}: {e}")
    return None

# ---------- پردازشگر داینامیک صف یادداشت‌ها (Dynamic Note Publisher) ----------

async def post_with_retry(http_client, url, json_payload=None, data=None, files=None, max_retries=3, initial_delay=2.0):
    """
    متد کمکی برای ارسال درخواست‌های HTTP با قابلیت تلاش مجدد خودکار در صورت قطعی شبکه یا خطای سرور واسط.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            if json_payload is not None:
                res = await http_client.post(url, json=json_payload)
            else:
                res = await http_client.post(url, data=data, files=files)
            
            # در صورتی که خطای سمت سرور (مثلا کد ۵۰۲ یا ۵۰۴ پروکسی گوگل) رخ دهد، تلاش مجدد می‌کنیم
            if res.status_code >= 500:
                logger.warning(
                    f"Relay proxy returned server error {res.status_code}. "
                    f"Attempt {attempt + 1}/{max_retries}. Retrying in {delay}s..."
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 1.5
                    continue
            return res
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.warning(
                f"HTTP network error occurred: {e}. "
                f"Attempt {attempt + 1}/{max_retries}. Retrying in {delay}s..."
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 1.5
                continue
            raise

async def handle_task_failure(http_client, base_url, bot_token, platform, task, status_code, response_text):
    owner_chat_id = task.get("owner_chat_id")
    if not owner_chat_id:
        logger.warning(f"No owner_chat_id found for task {task['id']}. Cannot send failure alert.")
        return

    # تلاش برای استخراج نام چت مقصد از متد getChat پیام‌رسان
    dest_title = task.get("chat_id")
    try:
        chat_url = f"{base_url}{bot_token}/getChat"
        chat_res = await http_client.get(chat_url, params={"chat_id": task["chat_id"]})
        if chat_res.status_code == 200:
            chat_data = chat_res.json().get("result", {})
            dest_title = chat_data.get("title") or chat_data.get("username") or chat_data.get("first_name") or task["chat_id"]
    except Exception as e:
        logger.error(f"Error fetching chat info in handle_task_failure: {e}")

    # تعیین علت مناسب بر اساس کد خطا
    reason = "خطای نامشخص"
    should_unregister = False
    if status_code == 403:
        reason = "ربات از گروه/کانال حذف شده یا دسترسی ارسال پیام ندارد."
        should_unregister = True
    elif status_code == 401:
        reason = "توکن ربات نامعتبر یا لغو شده است."
    elif status_code == 400:
        reason = "مشخصات مقصد نادرست است، متن پیام بیش از حد مجاز است، یا ربات دسترسی ادمین ندارد."
    elif status_code == 404:
        reason = "مقصد پیدا نشد یا حذف شده است."
        should_unregister = True

    if should_unregister:
        try:
            await api_client.unregister_chat(platform, task["chat_id"])
            logger.info(f"Unregistered unreachable chat {task['chat_id']} due to status {status_code}")
        except Exception as unreg_err:
            logger.error(f"Failed to unregister chat {task['chat_id']} in failure handler: {unreg_err}")

    action_type = "انتشار"
    if task["action"] == "edit":
        action_type = "ویرایش"
    elif task["action"] == "delete":
        action_type = "حذف"

    alert_text = (
        f"⚠️ <b>{action_type} یادداشت شما در «{format_text_for_telegram(str(dest_title))}» با خطا مواجه شد.</b>\n\n"
        f"❌ <b>علت:</b> {reason}\n"
        f"🆔 <b>شناسه مقصد:</b> <code>{task['chat_id']}</code>"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🔄 تلاش مجدد", "callback_data": f"retry_{task['id']}"},
                {"text": "📋 مشاهده متن یادداشت", "callback_data": f"view_{task['id']}"}
            ]
        ]
    }

    try:
        send_url = f"{base_url}{bot_token}/sendMessage"
        payload = {
            "chat_id": int(owner_chat_id),
            "text": alert_text,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }
        send_res = await http_client.post(send_url, json=payload)
        if send_res.status_code == 200:
            logger.info(f"Sent failure alert to owner {owner_chat_id} for task {task['id']}")
        else:
            logger.error(f"Failed to send failure alert: status={send_res.status_code}, text={send_res.text}")
    except Exception as e:
        logger.error(f"Error sending task failure alert: {e}")

async def task_processor():
    """
    پردازشگر صف یادداشت‌ها.
    به جای استفاده از کلاینت سراسری، با هر توکن شخصی کاربر به طور آنی ارسال می‌کند.
    """
    logger.info("Dynamic Task Processor started")
    async with httpx.AsyncClient(timeout=25.0) as http_client:
        while True:
            try:
                tasks = await api_client.fetch_tasks()
                for task in tasks:
                    tid = task["id"]
                    # Check if this task is currently rate-limited
                    if tid in rate_limit_delays:
                        if time.time() < rate_limit_delays[tid]:
                            logger.info(f"Task {tid} is currently rate limited (HTTP 429). Skipping.")
                            continue
                        else:
                            del rate_limit_delays[tid]

                    action = task["action"]
                    platform = task["platform"]
                    chat_id = task["chat_id"]
                    text = task["text"]
                    message_id = task.get("message_id")
                    bot_token = task.get("bot_token")
                    media_type = task.get("media_type", "text")
                    media_url = task.get("media_url")
                    
                    if not bot_token:
                        logger.warning(f"No custom bot token for task {tid}, skipping...")
                        continue
 
                    # ساخت URL برای متد API مناسب بر اساس پلتفرم
                    base_url = TELEGRAM_API_URL if platform == "telegram" else BALE_API_URL
                    if base_url.endswith("/"):
                        base_url = base_url[:-1]
 
                    try:
                        success = False
                        msg_id = message_id
                        res = None
                        
                        if action == "send":
                            if media_type in ("image", "video", "audio") and media_url:
                                internal_url = get_internal_media_url(media_url)
                                file_content = await download_file(http_client, internal_url)
                                if file_content:
                                    filename = media_url.split("/")[-1]
                                    
                                    # نگاشت صحیح نوع مدیا به فیلد مورد انتظار API تلگرام/بله
                                    file_field_name = "photo" if media_type == "image" else media_type
                                    
                                    # تشخیص خودکار MIME type فایل ارسالی
                                    import mimetypes
                                    mime_type, _ = mimetypes.guess_type(filename)
                                    if not mime_type:
                                        if media_type == "image":
                                            mime_type = "image/jpeg"
                                        elif media_type == "video":
                                            mime_type = "video/mp4"
                                        elif media_type == "audio":
                                            mime_type = "audio/mpeg"
                                        else:
                                            mime_type = "application/octet-stream"
                                            
                                    files = {file_field_name: (filename, file_content, mime_type)}
                                    data = {"chat_id": chat_id, "parse_mode": "HTML"}
                                    if text:
                                        data["caption"] = format_text_for_telegram(text)
                                    
                                    if media_type == "image":
                                        url = f"{base_url}{bot_token}/sendPhoto"
                                    elif media_type == "video":
                                        url = f"{base_url}{bot_token}/sendVideo"
                                    elif media_type == "audio":
                                        method = "sendAudio" if platform == "telegram" else "sendAudio"
                                        url = f"{base_url}{bot_token}/{method}"
                                    
                                    res = await post_with_retry(http_client, url, data=data, files=files)
                                    if res.status_code == 200:
                                        success = True
                                        msg_id = str(res.json().get("result", {}).get("message_id", ""))
                                    else:
                                        logger.error(f"send media failed for task {tid}: {res.text}")
                                        if res.status_code in (400, 401, 403, 404):
                                            logger.warning(f"Non-recoverable error for send media task {tid}. Completing to avoid queue blockage.")
                                            await handle_task_failure(http_client, base_url, bot_token, platform, task, res.status_code, res.text)
                                            success = True
                                else:
                                    # Fallback: if file couldn't be downloaded, send as text-only
                                    logger.warning(f"Could not download media for task {tid}, falling back to text-only send")
                                    url = f"{base_url}{bot_token}/sendMessage"
                                    payload = {"chat_id": chat_id, "text": format_text_for_telegram(text or "[فایل یافت نشد]"), "parse_mode": "HTML"}
                                    res = await post_with_retry(http_client, url, json_payload=payload)
                                    if res.status_code == 200:
                                        success = True
                                        msg_id = str(res.json().get("result", {}).get("message_id", ""))
                                    else:
                                        logger.error(f"fallback send failed for task {tid}: {res.text}")
                                        if res.status_code in (400, 401, 403, 404):
                                            await handle_task_failure(http_client, base_url, bot_token, platform, task, res.status_code, res.text)
                                            success = True
                            else:
                                url = f"{base_url}{bot_token}/sendMessage"
                                payload = {"chat_id": chat_id, "text": format_text_for_telegram(text), "parse_mode": "HTML"}
                                res = await post_with_retry(http_client, url, json_payload=payload)
                                if res.status_code == 200:
                                    success = True
                                    msg_id = str(res.json().get("result", {}).get("message_id", ""))
                                else:
                                    logger.error(f"send failed for task {tid}: {res.text}")
                                    if res.status_code in (400, 401, 403, 404):
                                        logger.warning(f"Non-recoverable error for send task {tid}. Completing to avoid queue blockage.")
                                        await handle_task_failure(http_client, base_url, bot_token, platform, task, res.status_code, res.text)
                                        success = True
                                
                        elif action == "edit" and message_id:
                            if media_type != "text" and media_url:
                                # ویرایش کپشن پیام‌های چندرسانه‌ای
                                url = f"{base_url}{bot_token}/editMessageCaption"
                                payload = {"chat_id": chat_id, "message_id": int(message_id), "caption": format_text_for_telegram(text), "parse_mode": "HTML"}
                            else:
                                url = f"{base_url}{bot_token}/editMessageText"
                                payload = {"chat_id": chat_id, "message_id": int(message_id), "text": format_text_for_telegram(text), "parse_mode": "HTML"}
 
                            res = await post_with_retry(http_client, url, json_payload=payload)
                            if res.status_code == 200:
                                success = True
                            else:
                                logger.error(f"edit failed for task {tid}: {res.text}")
                                if res.status_code in (400, 401, 403, 404):
                                    logger.warning(f"Non-recoverable error for edit task {tid}. Completing to avoid queue blockage.")
                                    await handle_task_failure(http_client, base_url, bot_token, platform, task, res.status_code, res.text)
                                    success = True
                                
                        elif action == "delete" and message_id:
                            url = f"{base_url}{bot_token}/deleteMessage"
                            payload = {"chat_id": chat_id, "message_id": int(message_id)}
                            res = await post_with_retry(http_client, url, json_payload=payload)
                            if res.status_code == 200:
                                success = True
                                msg_id = None
                            else:
                                logger.error(f"delete failed for task {tid}: {res.text}")
                                if res.status_code in (400, 401, 403, 404):
                                    logger.warning(f"Non-recoverable error for delete task {tid}. Completing to avoid queue blockage.")
                                    await handle_task_failure(http_client, base_url, bot_token, platform, task, res.status_code, res.text)
                                    success = True
                                    msg_id = None
 
                        if not success and res is not None and res.status_code == 429:
                            retry_after = 5.0
                            try:
                                retry_after = float(res.headers.get("Retry-After", 5.0))
                            except (ValueError, TypeError):
                                pass
                            logger.warning(f"Rate limit HTTP 429 hit for task {tid}. Delaying task for {retry_after}s.")
                            rate_limit_delays[tid] = time.time() + retry_after

                        if success:
                            await api_client.complete_task(tid, msg_id)
                            logger.info(f"Successfully processed {action} task {tid} for user's bot")
                            
                    except Exception as e:
                        logger.error(f"HTTP call failed for task {tid}: {e}")
 
            except Exception as e:
                logger.error(f"Error in task_processor loop: {e}")
                
            await asyncio.sleep(5)

# ---------- اجرای برنامه ----------

async def main():
    logger.info("Starting Tafakor dynamic Bot Runner...")
    
    # اجرای همزمان پردازشگر تسک‌ها و مدیر داینامیک ربات‌ها
    await asyncio.gather(
        dynamic_bot_manager(),
        task_processor()
    )

if __name__ == "__main__":
    asyncio.run(main())