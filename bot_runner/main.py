import os
import asyncio
import httpx
import logging
import html
import re
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
            logger.info(f"Automatically registered chat_id {chat_id} for owner {phone} ({platform}) via custom_start")
        except Exception as e:
            logger.error(f"Failed to auto-register owner chat_id: {e}")

    await update.message.reply_text(
        f"🧠 <b>به ربات اختصاصی تفکر خوش آمدید!</b>\n\n"
        f"این ربات به صورت اختصاصی به حساب تفکر شما با شماره <code>{format_text_for_telegram(phone)}</code> متصل است.\n\n"
        "💡 <b>راه‌های اتصال مقصد جدید (گروه یا کانال):</b>\n\n"
        "1️⃣ <b>روش اول (سریع‌ترین):</b> ربات را به عنوان مدیر (Admin) به کانال یا گروه خود اضافه کنید و دستور <code>/connect</code> را داخل آن بفرستید.\n\n"
        "2️⃣ <b>روش دوم (دستی):</b> شناسه عددی (Chat ID) گروه یا کانال خود را مستقیماً در این چت ارسال کنید. (مثلاً: <code>-100123456789</code>).\n\n"
        "🔹 برای مشاهده و مدیریت لیست مقاصد متصل، از دکمه زیر صفحه استفاده کنید:",
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
        "۳. دستور <code>/connect</code> یا <code>/register</code> را در کانال یا گروه ارسال کنید.\n"
        "۴. ربات به طور خودکار آن را ثبت و پیام تایید ارسال می‌کند.\n\n"
        "🔹 <b>نحوه اتصال با شناسه چت (مستقیم):</b>\n"
        "اگر شناسه عددی چت خود را دارید (معمولاً شناسه کانال‌ها با <code>-100</code> شروع می‌شود)، آن را مستقیماً به همین چت ارسال کنید تا ثبت شود.\n\n"
        "🔹 <b>مدیریت مقاصد:</b>\n"
        "از دکمه «📋 لیست مقاصد (کانال‌ها/گروه‌ها)» برای مشاهده، حذف و پیش‌فرض کردن استفاده کنید.",
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
    
    # در صورتی که ربات به عنوان ادمین یا عضو اضافه شده باشد
    if new_status in ("administrator", "member"):
        user_id = context.bot_data.get("user_id")
        platform = context.bot_data.get("platform")
        phone = context.bot_data.get("phone")
        label = chat.title or f"Chat {chat_id}"
        
        logger.info(f"Auto-registering chat {chat_id} ({label}) for user {user_id} ({platform})")
        try:
            # فراخوانی وب‌سرویس ثبت مقصد به صورت مستقیم
            await api_client.register_destination(user_id, platform, chat_id, label)
            
            # ارسال پیام خصوصی تایید به صاحب ربات
            await context.bot.send_message(
                chat_id=int(my_chat_member.from_user.id),
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

async def send_destinations_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مقاصد متصل با قابلیت فعال/غیرفعال‌سازی و حذف کامل"""
    chat = update.effective_chat
    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    
    destinations = await api_client.get_destinations(user_id, platform)
    
    if not destinations:
        await update.effective_message.reply_text(
            "📭 در حال حاضر هیچ گروه یا کانالی متصل نشده است.\n\n"
            "برای اضافه کردن مقصد جدید، دکمه «➕ راهنمای اتصال مقصد» را کلیک کنید یا شناسه چت را بفرستید."
        )
        return

    await update.effective_message.reply_text(
        "📋 <b>لیست مقاصد متصل شده به تفکر:</b>",
        parse_mode="HTML"
    )
    
    for dest in destinations:
        dest_id = dest["id"]
        label = dest["label"]
        chat_id = dest["chat_id"]
        is_active = dest.get("is_active", True)
        
        status_text = "🟢 فعال" if is_active else "🔴 غیرفعال"
        
        text = (
            f"📢 <b>نام:</b> {format_text_for_telegram(label)}\n"
            f"🆔 <b>شناسه:</b> <code>{chat_id}</code>\n"
            f"📊 <b>وضعیت:</b> {status_text}"
        )
        
        # ساخت دکمه‌های شیشه‌ای (Inline Keyboard)
        buttons = []
        if is_active:
            buttons.append(InlineKeyboardButton("🔴 غیرفعال‌سازی", callback_data=f"toggle_{dest_id}"))
        else:
            buttons.append(InlineKeyboardButton("🟢 فعال‌سازی", callback_data=f"toggle_{dest_id}"))
        buttons.append(InlineKeyboardButton("❌ حذف", callback_data=f"delete_{dest_id}"))
        
        reply_markup = InlineKeyboardMarkup([buttons])
        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup
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

async def handle_any_message_or_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message or not message.text:
        return

    text = message.text.strip()
    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    phone = context.bot_data.get("phone", "نامشخص")

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

        # د) وارد کردن شناسه عددی چت برای ثبت مستقیم
        clean_text = text.lstrip('-')
        if clean_text.isdigit():
            chat_id = text
            logger.info(f"Attempting manual chat registration for id: {chat_id}")
            try:
                chat_obj = await context.bot.get_chat(int(chat_id))
                label = chat_obj.title or chat_obj.username or f"Chat {chat_id}"
                await api_client.register_destination(user_id, platform, chat_id, label)
                await message.reply_text(
                    f"✅ <b>ثبت مقصد با موفقیت انجام شد!</b>\n\n"
                    f"📢 نام مقصد: <code>{format_text_for_telegram(label)}</code>\n"
                    f"🆔 شناسه: <code>{chat_id}</code>\n\n"
                    f"این چت به مقاصد انتشار حساب شما اضافه شد.",
                    parse_mode="HTML"
                )
            except Exception as e:
                await message.reply_text(
                    f"❌ خطا در دسترسی به چت با شناسه {chat_id}.\n\n"
                    f"مطمئن شوید:\n"
                    f"۱. شناسه را درست وارد کرده‌اید (شناسه کانال‌ها معمولاً با -100 شروع می‌شود).\n"
                    f"۲. ربات را در آن کانال/گروه عضو کرده و دسترسی مدیریت (Admin) به آن داده‌اید.\n\n"
                    f"جزئیات خطا: {e}"
                )
            return

        # ه) پیام متنی متفرقه در چت خصوصی
        await custom_start(update, context)

# ---------- مدیریت داینامیک کلاینت‌های ربات‌ها ----------

async def run_single_bot(bot_key: str, token: str, platform: str, user_id: int, phone: str):
    """راه‌اندازی کلاینت مستقل ربات با کتابخانه python-telegram-bot"""
    logger.info(f"Starting custom bot task for user {user_id} ({platform})")
    
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

    # هندلرهای ربات اختصاصی
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT | filters.ChatType.CHANNEL, handle_any_message_or_post))

    try:
        async with app:
            await app.start()
            poll_interval = 2.0 if platform == "bale" else 0.0
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, poll_interval=poll_interval)
            await asyncio.Event().wait()
    except Exception as e:
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
                bot_key = f"{platform}_{uid}"
                
                # اگر ربات در حال اجرا نیست، آن را استارت بزن
                if bot_key not in running_bots:
                    logger.info(f"New active bot detected: {bot_key}, launching...")
                    task = asyncio.create_task(run_single_bot(bot_key, token, platform, uid, phone))
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
                                        if res.status_code in (400, 403, 404):
                                            logger.warning(f"Non-recoverable error for send media task {tid}. Completing to avoid queue blockage.")
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
                                        if res.status_code in (400, 403, 404):
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
                                    if res.status_code in (400, 403, 404):
                                        logger.warning(f"Non-recoverable error for send task {tid}. Completing to avoid queue blockage.")
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
                                if res.status_code in (400, 403, 404):
                                    logger.warning(f"Non-recoverable error for edit task {tid}. Completing to avoid queue blockage.")
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
                                if res.status_code in (400, 403, 404):
                                    logger.warning(f"Non-recoverable error for delete task {tid}. Completing to avoid queue blockage.")
                                    success = True
                                    msg_id = None
 
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