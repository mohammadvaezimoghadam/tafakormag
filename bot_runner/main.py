import os
import asyncio
import httpx
import logging
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
    await update.message.reply_text(
        f"🧠 *به ربات اختصاصی تفکر خوش آمدید!*\n\n"
        f"این ربات به صورت اختصاصی به حساب تفکر شما با شماره `{phone}` متصل است.\n\n"
        "💡 *راه‌های اتصال مقصد جدید (گروه یا کانال):*\n\n"
        "1️⃣ **روش اول (سریع‌ترین):** ربات را به عنوان مدیر (Admin) به کانال یا گروه خود اضافه کنید و دستور `/connect` را داخل آن بفرستید.\n\n"
        "2️⃣ **روش دوم (دستی):** شناسه عددی (Chat ID) گروه یا کانال خود را مستقیماً در این چت ارسال کنید. (مثلاً: `-100123456789`).\n\n"
        "🔹 برای مشاهده و مدیریت لیست مقاصد متصل، از دکمه زیر صفحه استفاده کنید:",
        parse_mode="Markdown",
        reply_markup=get_custom_main_keyboard()
    )

async def custom_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.bot_data.get("phone", "نامشخص")
    await update.message.reply_text(
        f"🔌 *وضعیت اتصال به تفکر:*\n\n"
        f"این ربات اختصاصی با موفقیت به حساب تفکر با شماره `{phone}` متصل است و آماده انتشار یادداشت‌های شما می‌باشد.",
        parse_mode="Markdown",
        reply_markup=get_custom_main_keyboard()
    )

async def custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *راهنمای اتصال مقاصد انتشار*\n\n"
        "برای اینکه یادداشت‌های شما در کانال یا گروه منتشر شوند، باید آن‌ها را متصل کنید:\n\n"
        "🔹 **نحوه اتصال خودکار کانال/گروه:**\n"
        "۱. ربات را به گروه یا کانال خود دعوت کنید.\n"
        "۲. ربات را مدیر (Admin) با دسترسی ارسال پیام کنید.\n"
        "۳. دستور `/connect` یا `/register` را در کانال یا گروه ارسال کنید.\n"
        "۴. ربات به طور خودکار آن را ثبت و پیام تایید ارسال می‌کند.\n\n"
        "🔹 **نحوه اتصال با شناسه چت (مستقیم):**\n"
        "اگر شناسه عددی چت خود را دارید (معمولاً شناسه کانال‌ها با `-100` شروع می‌شود)، آن را مستقیماً به همین چت ارسال کنید تا ثبت شود.\n\n"
        "🔹 **مدیریت مقاصد:**\n"
        "از دکمه «📋 لیست مقاصد (کانال‌ها/گروه‌ها)» برای مشاهده، حذف و پیش‌فرض کردن استفاده کنید.",
        parse_mode="Markdown",
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
                    f"✅ *ثبت خودکار مقصد موفقیت‌آمیز بود!*\n\n"
                    f"📢 نام مقصد: `{label}`\n"
                    f"🆔 شناسه: `{chat_id}`\n\n"
                    f"این چت با موفقیت به مقاصد انتشار حساب تفکر شما (`{phone}`) اضافه شد."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Auto-registration failed: {e}")

async def send_destinations_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مقاصد متصل با قابلیت حذف و پیش‌فرض کردن"""
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

    await update.effective_message.reply_text("📋 *لیست مقاصد متصل شده به تفکر:*")
    
    for dest in destinations:
        dest_id = dest["id"]
        label = dest["label"]
        chat_id = dest["chat_id"]
        is_default = dest.get("is_default", False)
        
        default_status = "⭐ [پیش‌فرض]" if is_default else "◽ [معمولی]"
        
        text = (
            f"📢 *نام:* {label}\n"
            f"🆔 *شناسه:* `{chat_id}`\n"
            f"📊 *وضعیت:* {default_status}"
        )
        
        # ساخت دکمه‌های شیشه‌ای (Inline Keyboard)
        buttons = []
        if not is_default:
            buttons.append(InlineKeyboardButton("⭐ پیش‌فرض", callback_data=f"default_{dest_id}"))
        buttons.append(InlineKeyboardButton("❌ حذف", callback_data=f"delete_{dest_id}"))
        
        reply_markup = InlineKeyboardMarkup([buttons])
        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = context.bot_data.get("user_id")
    platform = context.bot_data.get("platform")
    
    if data.startswith("default_"):
        dest_id = int(data.split("_")[1])
        success = await api_client.set_default_destination(user_id, platform, dest_id)
        if success:
            await query.edit_message_text(
                text=query.message.text + "\n\n✅ با موفقیت به عنوان پیش‌فرض انتخاب شد."
            )
        else:
            await query.edit_message_text(
                text=query.message.text + "\n\n❌ خطا در تنظیم پیش‌فرض."
            )
            
    elif data.startswith("delete_"):
        dest_id = int(data.split("_")[1])
        success = await api_client.delete_destination(user_id, platform, dest_id)
        if success:
            await query.edit_message_text(
                text=query.message.text + "\n\n❌ این مقصد با موفقیت حذف شد."
            )
        else:
            await query.edit_message_text(
                text=query.message.text + "\n\n❌ خطا در حذف مقصد."
            )

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
                f"✅ *ثبت مقصد موفقیت‌آمیز بود!*\n\n"
                f"📢 نام مقصد: `{label}`\n"
                f"🆔 شناسه: `{chat_id}`\n\n"
                f"این چت با موفقیت به مقاصد انتشار حساب تفکر شما (`{phone}`) اضافه شد.",
                parse_mode="Markdown"
            )
        except Exception as e:
            await message.reply_text(f"⚠️ ثبت مقصد انجام نشد یا قبلاً ثبت شده است.\nشناسه چت: `{chat_id}`\nجزئیات: {e}")
        return

    # ۲. مدیریت چت خصوصی ربات
    if chat.type == "private":
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
                    f"✅ *ثبت مقصد با موفقیت انجام شد!*\n\n"
                    f"📢 نام مقصد: `{label}`\n"
                    f"🆔 شناسه: `{chat_id}`\n\n"
                    f"این چت به مقاصد انتشار حساب شما اضافه شد.",
                    parse_mode="Markdown"
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
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
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
            active_bots = await api_client.get_active_custom_bots()
            active_keys = set()
            
            for bot in active_bots:
                uid = bot["user_id"]
                platform = bot["platform"]
                token = bot["token"].strip()
                phone = bot["phone"]
                bot_key = f"{platform}_{uid}"
                active_keys.add(bot_key)
                
                # اگر ربات در حال اجرا نیست، آن را استارت بزن
                if bot_key not in running_bots:
                    logger.info(f"New active bot detected: {bot_key}, launching...")
                    task = asyncio.create_task(run_single_bot(bot_key, token, platform, uid, phone))
                    running_bots[bot_key] = task
            
            # اگر رباتی دیگر در لیست فعال نیست، آن را متوقف کن
            for bot_key in list(running_bots.keys()):
                if bot_key not in active_keys:
                    logger.info(f"Bot {bot_key} is no longer active, terminating task...")
                    task = running_bots.pop(bot_key)
                    task.cancel()
                    
        except Exception as e:
            logger.error(f"Error in dynamic_bot_manager: {e}")
            
        await asyncio.sleep(20)

# ---------- پردازشگر داینامیک صف یادداشت‌ها (Dynamic Note Publisher) ----------

async def task_processor():
    """
    پردازشگر صف یادداشت‌ها.
    به جای استفاده از کلاینت سراسری، با هر توکن شخصی کاربر به طور آنی ارسال می‌کند.
    """
    logger.info("Dynamic Task Processor started")
    async with httpx.AsyncClient(timeout=10.0) as http_client:
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
                            url = f"{base_url}{bot_token}/sendMessage"
                            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
                            res = await http_client.post(url, json=payload)
                            if res.status_code == 200:
                                success = True
                                msg_id = str(res.json().get("result", {}).get("message_id", ""))
                            else:
                                logger.error(f"send failed for task {tid}: {res.text}")
                                
                        elif action == "edit" and message_id:
                            url = f"{base_url}{bot_token}/editMessageText"
                            payload = {"chat_id": chat_id, "message_id": int(message_id), "text": text, "parse_mode": "Markdown"}
                            res = await http_client.post(url, json=payload)
                            if res.status_code == 200:
                                success = True
                            else:
                                logger.error(f"edit failed for task {tid}: {res.text}")
                                
                        elif action == "delete" and message_id:
                            url = f"{base_url}{bot_token}/deleteMessage"
                            payload = {"chat_id": chat_id, "message_id": int(message_id)}
                            res = await http_client.post(url, json=payload)
                            if res.status_code == 200:
                                success = True
                                msg_id = None
                            else:
                                logger.error(f"delete failed for task {tid}: {res.text}")

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