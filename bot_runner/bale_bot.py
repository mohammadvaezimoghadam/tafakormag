import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError

from config import (
    BALE_BOT_TOKEN,
    BALE_BASE_URL,
    BALE_FILE_URL,
    POLL_INTERVAL
)
from api_client import APIClient
from logger_config import setup_logger

logger = setup_logger("bale_bot", "bale.log")
api_client = APIClient()

# ---------- منوی اصلی (دکمه‌های دائمی) ----------

def get_main_keyboard():
    """ساخت منوی دائمی با ReplyKeyboardMarkup"""
    keyboard = [
        [KeyboardButton("📋 کانال‌ها و گروه‌های من")],
        [KeyboardButton("🔗 اتصال گروه/کانال جدید")],
        [KeyboardButton("📱 ثبت/بروزرسانی شماره موبایل", request_contact=True)],
        [KeyboardButton("❓ راهنما")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_start_keyboard():
    """ساخت منوی ثبت‌نام/شروع برای کاربرانی که هنوز متصل نشده‌اند"""
    keyboard = [
        [KeyboardButton("📱 ثبت شماره موبایل", request_contact=True)],
        [KeyboardButton("❓ راهنما")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def is_user_linked(chat_id: int) -> bool:
    """بررسی اینکه آیا چت کاربر متصل به حسابی در تفکر است یا خیر"""
    try:
        user_id = await api_client.get_user_id_by_chat("bale", chat_id)
        return bool(user_id)
    except Exception:
        return False


WELCOME_TEXT = (
    "🧠 به ربات تفکر خوش آمدید!\n\n"
    "🎯 این ربات به شما کمک می‌کند یادداشت‌های هوشمند خود را از طریق اپلیکیشن تفکر مدیریت کنید "
    "و آن‌ها را به کانال‌ها و گروه‌های تلگرام و بله ارسال کنید.\n\n"
    "📌 برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:"
)

HELP_TEXT = (
    "📖 *راهنمای ربات تفکر*\n\n"
    "🔹 *اتصال حساب کاربری:*\n"
    "۱. وارد اپلیکیشن تفکر شوید.\n"
    "۲. از بخش تنظیمات، گزینه «اتصال به ربات» را انتخاب کنید.\n"
    "۳. توکن نمایش‌داده‌شده را کپی کرده و در این چت بفرستید.\n\n"
    "🔹 *اتصال گروه/کانال:*\n"
    "۱. ربات را به گروه یا کانال مورد نظر خود *افزوده (Add)* کنید.\n"
    "۲. ربات را در آن گروه/کانال *ادمین (Admin)* کنید.\n"
    "۳. در همان گروه/کانال، دستور `/register` را ارسال کنید.\n"
    "۴. پیام تأیید ثبت به‌صورت *خصوصی* برای شما ارسال خواهد شد.\n\n"
    "🔹 *مدیریت مقصدها:*\n"
    "از دکمه «📋 کانال‌ها و گروه‌های من» برای مشاهده و انتخاب مقصد پیش‌فرض استفاده کنید.\n\n"
    "🔹 *نکته مهم:*\n"
    "یادداشت‌های شما از سمت تفکر به مقصد پیش‌فرض یا گروه/کانال انتخابی ارسال می‌شوند.\n"
    "پیام‌های موفقیت و خطا *فقط* در چت خصوصی ربات نمایش داده می‌شوند."
)

HOW_TO_REGISTER_TEXT = (
    "📝 *راهنمای ثبت گروه/کانال جدید:*\n\n"
    "1️⃣ ربات را به گروه یا کانال مورد نظر *افزوده (Add)* کنید.\n"
    "2️⃣ ربات را *ادمین (Admin)* کنید (دسترسی ارسال پیام نیاز است).\n"
    "3️⃣ در همان گروه یا کانال، دستور `/register` را تایپ و ارسال کنید.\n\n"
    "⚠️ توجه: پیام تأیید ثبت به‌صورت *خصوصی* برای شما ارسال می‌شود، نه در گروه."
)

# ---------- Handlers ----------

async def register_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت chat_id گروه/کانال و ثبت آن به عنوان مقصد کاربر.
    پیام موفقیت/خطا به صورت خصوصی به کاربر ارسال می‌شود، نه در گروه."""
    chat = update.effective_chat
    chat_id = str(chat.id)
    user = update.effective_user

    if chat.type not in ("group", "supergroup", "channel"):
        await update.message.reply_text(
            "⚠️ این دستور فقط در گروه‌ها و کانال‌ها قابل استفاده است."
        )
        return

    try:
        user_id = await api_client.get_user_id_by_chat("bale", user.id)
        label = chat.title or f"Chat {chat_id}"
        await api_client.register_destination(user_id, "bale", chat_id, label)

        # ارسال پیام موفقیت به صورت خصوصی به کاربر
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"✅ *مقصد با موفقیت ثبت شد!*\n\n"
                f"📌 نام: {label}\n"
                f"🆔 شناسه: `{chat_id}`\n\n"
                f"از این پس یادداشت‌های شما می‌توانند به این گروه/کانال ارسال شوند."
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Registered destination: {label} ({chat_id}) for user {user_id}")
    except Exception as e:
        # ارسال خطا به صورت خصوصی به کاربر
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "❌ *خطا در ثبت مقصد*\n\n"
                "لطفاً مطمئن شوید:\n"
                "• حساب کاربری شما به ربات متصل است (ابتدا توکن را در چت خصوصی ربات ارسال کنید).\n"
                "• ربات در گروه/کانال ادمین است."
            ),
            parse_mode="Markdown"
        )
        logger.warning(f"Registration failed: {e}")


async def destinations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مقاصد متصل با قابلیت فعال/غیرفعال‌سازی و حذف کامل"""
    chat_id = update.effective_chat.id
    try:
        user_id = await api_client.get_user_id_by_chat("bale", chat_id)
        destinations = await api_client.get_destinations(user_id, "bale")
        if not destinations:
            await update.message.reply_text(
                "🔍 شما هنوز هیچ مقصدی ثبت نکرده‌اید.\n\n"
                "برای ثبت گروه/کانال جدید:\n"
                "۱. ربات را به گروه/کانال اضافه کنید.\n"
                "۲. در آن گروه/کانال دستور `/register` را ارسال کنید.",
                parse_mode="Markdown"
            )
            return

        await update.message.reply_text("📋 *لیست مقاصد متصل شده به تفکر:*")

        for dest in destinations:
            dest_id = dest["id"]
            label = dest.get("label", "بدون نام")
            chat_num_id = dest["chat_id"]
            is_active = dest.get("is_active", True)

            status_text = "🟢 فعال" if is_active else "🔴 غیرفعال"

            text = (
                f"📢 *نام:* {label}\n"
                f"🆔 *شناسه:* `{chat_num_id}`\n"
                f"📊 *وضعیت:* {status_text}"
            )

            buttons = []
            if is_active:
                buttons.append(InlineKeyboardButton("🔴 غیرفعال‌سازی", callback_data=f"toggle_{dest_id}"))
            else:
                buttons.append(InlineKeyboardButton("🟢 فعال‌سازی", callback_data=f"toggle_{dest_id}"))
            buttons.append(InlineKeyboardButton("❌ حذف", callback_data=f"delete_{dest_id}"))

            reply_markup = InlineKeyboardMarkup([buttons])
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    except Exception as e:
        await update.message.reply_text(
            "❌ خطا در دریافت مقصدها.\n"
            "لطفاً ابتدا حساب خود را با ارسال توکن به ربات متصل کنید."
        )
        logger.error(f"destinations_menu error: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    if data == "how_to_register":
        await query.edit_message_text(
            HOW_TO_REGISTER_TEXT,
            parse_mode="Markdown"
        )
    elif data.startswith("toggle_"):
        try:
            dest_id = int(data.split("_")[1])
            user_id = await api_client.get_user_id_by_chat("bale", chat_id)
            result = await api_client.toggle_active_destination(user_id, "bale", dest_id)
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
                await query.edit_message_text(
                    text=new_text,
                    reply_markup=reply_markup
                )
            else:
                await query.answer("❌ خطا در تغییر وضعیت مقصد.", show_alert=True)
        except Exception as e:
            await query.answer("❌ مشکلی پیش آمد، دوباره تلاش کنید.", show_alert=True)
            logger.error(f"button_callback error: {e}")

    elif data.startswith("delete_"):
        try:
            dest_id = int(data.split("_")[1])
            user_id = await api_client.get_user_id_by_chat("bale", chat_id)
            success = await api_client.delete_destination(user_id, "bale", dest_id)
            if success:
                await query.edit_message_text(
                    text=query.message.text + "\n\n❌ این مقصد با موفقیت حذف شد."
                )
            else:
                await query.answer("❌ خطا در حذف مقصد.", show_alert=True)
        except Exception as e:
            await query.answer("❌ مشکلی پیش آمد، دوباره تلاش کنید.", show_alert=True)
            logger.error(f"button_callback delete error: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if await is_user_linked(chat_id):
        await update.message.reply_text(
            WELCOME_TEXT,
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "🧠 *به ربات تفکر خوش آمدید!*\n\n"
            "برای دریافت آسان و سریع کد تایید ورود در همین ربات، لطفاً با کلیک بر روی دکمه زیر شماره موبایل خود را به اشتراک بگذارید یا توکن اتصال از اپلیکیشن را ارسال کنید.",
            parse_mode="Markdown",
            reply_markup=get_start_keyboard()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if await is_user_linked(chat_id):
        reply_markup = get_main_keyboard()
    else:
        reply_markup = get_start_keyboard()

    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    chat_id = update.effective_chat.id

    try:
        await update.message.delete()
    except TelegramError:
        pass

    try:
        await api_client.verify_link(token, "bale", chat_id)
        await context.bot.send_message(
            chat_id,
            "✅ *حساب شما با موفقیت به ربات متصل شد!*\n\n"
            "اکنون می‌توانید:\n"
            "• یادداشت‌های خود را از طریق اپ تفکر همگام‌سازی کنید.\n"
            "• با استفاده از دکمه‌های زیر، گروه‌ها و کانال‌های خود را مدیریت کنید.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"User {update.effective_user.id} connected")
    except Exception as e:
        linked = await is_user_linked(chat_id)
        reply_markup = get_main_keyboard() if linked else get_start_keyboard()
        await context.bot.send_message(
            chat_id,
            "❌ *توکن نامعتبر یا منقضی شده است*\n\n"
            "لطفاً دوباره از اپلیکیشن تفکر توکن جدید دریافت کنید و آن را ارسال نمایید.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.warning(f"Connection failed: {e}")


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت شماره موبایل از طریق اشتراک‌گذاری مخاطب (Contact)"""
    contact = update.message.contact
    chat_id = update.effective_chat.id
    user = update.effective_user

    if not contact:
        return

    # بررسی امنیت: آیا مخاطب ارسال شده متعلق به خود فرستنده است؟
    if contact.user_id and contact.user_id != user.id:
        await update.message.reply_text(
            "⚠️ خطا: لطفاً فقط شماره موبایل خود را به اشتراک بگذارید (از دکمه ثبت شماره موبایل استفاده کنید).",
            reply_markup=get_start_keyboard()
        )
        return

    phone = contact.phone_number.strip()

    try:
        # همگام‌سازی شماره تلفن با بک‌اند
        await api_client.register_phone_chat("bale", phone, chat_id)

        await update.message.reply_text(
            f"✅ *شماره موبایل شما با موفقیت ثبت شد!*\n\n"
            f"📱 شماره ثبت شده: `{phone}`\n\n"
            f"از این پس می‌توانید برای دریافت سریع کد ورود به اپلیکیشن تفکر، "
            f"از این ربات استفاده کنید. کدهای تأیید مستقیماً همین‌جا برای شما ارسال خواهند شد.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Phone registered via Bale contact sharing for user {user.id}: {phone}")
    except Exception as e:
        await update.message.reply_text(
            "❌ خطا در ثبت شماره موبایل.\n"
            "لطفاً مطمئن شوید شماره به درستی ارسال شده یا بعداً تلاش کنید.",
            reply_markup=get_start_keyboard()
        )
        logger.error(f"Contact registration failed: {e}")



async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش دکمه‌های منوی اصلی (ReplyKeyboardMarkup)"""
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if text == "📋 کانال‌ها و گروه‌های من":
        await destinations_menu(update, context)
    elif text == "🔗 اتصال گروه/کانال جدید":
        await update.message.reply_text(
            HOW_TO_REGISTER_TEXT,
            parse_mode="Markdown"
        )
    elif text == "❓ راهنما":
        await help_command(update, context)


# ---------- Task Processor ----------

async def task_processor(app: Application):
    logger.info("Bale task processor started")
    while True:
        try:
            tasks = await api_client.fetch_tasks()
            for task in tasks:
                if task.get("platform") != "bale":
                    continue
                tid = task["id"]
                action = task["action"]
                chat_id = task["chat_id"]
                text = task["text"]
                message_id = task.get("message_id")

                try:
                    dest_chat_id = int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id
                    if action == "send":
                        msg = await app.bot.send_message(
                            dest_chat_id, text, parse_mode="Markdown"
                        )
                        await api_client.complete_task(tid, str(msg.message_id))
                        logger.info(f"Sent message for task {tid}")

                    elif action == "edit" and message_id:
                        await app.bot.edit_message_text(
                            text=text,
                            chat_id=dest_chat_id,
                            message_id=int(message_id),
                            parse_mode="Markdown"
                        )
                        await api_client.complete_task(tid, message_id)
                        logger.info(f"Edited message for task {tid}")

                    elif action == "delete" and message_id:
                        await app.bot.delete_message(dest_chat_id, int(message_id))
                        await api_client.complete_task(tid, message_id)
                        logger.info(f"Deleted message for task {tid}")

                except TelegramError as e:
                    logger.error(f"Task {tid} failed: {e}")

        except Exception as e:
            logger.error(f"Task loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)


# ---------- Run ----------

async def run():
    if not BALE_BOT_TOKEN:
        logger.error("BALE_BOT_TOKEN is not set!")
        return

    app = (
        ApplicationBuilder()
        .token(BALE_BOT_TOKEN)
        .base_url(BALE_BASE_URL)
        .base_file_url(BALE_FILE_URL)
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("register", register_chat))
    app.add_handler(CommandHandler("destinations", destinations_menu))

    # Contact sharing handler (must be registered before generic text/token handler)
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Callback query handler (for inline buttons)
    app.add_handler(CallbackQueryHandler(button_callback))

    # Menu button handlers
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^(📋 کانال‌ها و گروه‌های من|🔗 اتصال گروه/کانال جدید|❓ راهنما)$"),
        handle_menu_buttons
    ))

    # Token handler (must be last among message handlers to not interfere)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token))

    async with app:
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        task = asyncio.create_task(task_processor(app))
        logger.info("Bale bot is polling and ready...")

        try:
            await asyncio.Event().wait()
        finally:
            task.cancel()
            await app.updater.stop()
            await app.stop()