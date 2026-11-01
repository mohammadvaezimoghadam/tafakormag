import os
import sys
import uuid
import logging
import django

# تنظیم PYTHONPATH و پیکربندی محلی جنگو
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'note_platform.settings')
django.setup()

from django.conf import settings
from django.core.cache import cache
from apps.accounts.models import User
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# تنظیمات لاگر
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("bale_otp_bot")

def get_contact_keyboard():
    """ساخت دکمه ارسال مخاطب امن"""
    keyboard = [[KeyboardButton("📱 ارسال شماره موبایل (اشتراک مخاطب)", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع مجدد یا خوش‌آمدگویی و صدور خودکار کد برای کاربران آشنا"""
    if update.effective_chat.type != "private":
        await update.message.reply_text("⚠️ این ربات فقط در چت‌های خصوصی قابل استفاده است.")
        return

    chat_id = str(update.effective_user.id)
    from asgiref.sync import sync_to_async

    # بررسی اینکه آیا کاربر قبلاً شماره خود را متصل کرده است
    user = await sync_to_async(User.objects.filter(bale_chat_id=chat_id).first)()
    if user:
        phone = user.phone
        otp = str(uuid.uuid4().int)[:4]
        cache_key = f"otp_{phone}"
        await sync_to_async(cache.set)(cache_key, otp, timeout=120)
        
        logger.info(f"[OTP BALE] Automatically set code '{otp}' in cache for existing phone: {phone}")
        
        await update.message.reply_text(
            f"🔑 *کد ورود جدید شما با موفقیت تولید شد:*\n\n"
            f"👑 `{otp}`\n\n"
            f"⚠️ *توجه مهم:* این کد فقط برای شماره موبایل **`{phone}`** معتبر است. "
            f"لطفاً در صفحه ورود تفکر، حتماً همین شماره موبایل **`{phone}`** را وارد کنید؛ "
            f"در غیر این صورت خطای منقضی شدن کد را دریافت خواهید کرد.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "🧠 به ربات دریافت کد تایید تفکر خوش آمدید!\n\n"
        "برای دریافت کد ورود به وب‌سایت، لطفاً با کلیک روی دکمه زیر شماره موبایل خود را به اشتراک بگذارید:",
        reply_markup=get_contact_keyboard()
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مخاطب، تایید، ثبت chat_id، نرمال‌سازی شماره و ذخیره کد در کش جنگو"""
    if update.effective_chat.type != "private":
        return

    contact = update.message.contact
    if not contact:
        await update.message.reply_text(
            "⚠️ لطفاً برای دریافت کد، فقط از دکمه زیر صفحه برای ارسال شماره استفاده کنید.",
            reply_markup=get_contact_keyboard()
        )
        return

    # برای امنیت: چت‌آیدی فرستنده باید با چت‌آیدی مخاطب یکسان باشد
    if str(contact.user_id) != str(update.effective_user.id):
        await update.message.reply_text(
            "❌ خطا در احراز هویت. شماره ارسال شده متعلق به حساب جاری شما نیست.",
            reply_markup=get_contact_keyboard()
        )
        return

    raw_phone = str(contact.phone_number).strip()
    
    # نرمال‌سازی شماره تلفن ایران
    phone = raw_phone
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    elif phone.startswith("98"):
        phone = "0" + phone[2:]
    elif not phone.startswith("0") and len(phone) == 10:
        phone = "0" + phone

    # اطمینان از طول ۱۱ رقمی استاندارد
    if not phone.startswith("09") or len(phone) != 11:
        await update.message.reply_text(
            f"❌ شماره موبایل استخراج‌شده معتبر نیست: {phone}\n"
            "لطفاً مجدداً تلاش کنید.",
            reply_markup=get_contact_keyboard()
        )
        return

    # تولید کد ورود
    otp = str(uuid.uuid4().int)[:4]
    cache_key = f"otp_{phone}"
    
    # ذخیره در کش دیتابیس مشترک جنگو به مدت ۱۲۰ ثانیه
    from asgiref.sync import sync_to_async
    await sync_to_async(cache.set)(cache_key, otp, timeout=120)
    
    # ذخیره شناسه چت بله در پروفایل کاربر برای دفعات بعدی
    try:
        user, created = await sync_to_async(User.objects.get_or_create)(phone=phone)
        user.bale_chat_id = str(update.effective_user.id)
        await sync_to_async(user.save)()
        logger.info(f"[OTP BALE] Associated chat_id {update.effective_user.id} with phone {phone}")
    except Exception as e:
        logger.error(f"[OTP BALE] Failed to save bale_chat_id: {e}")
    
    logger.info(f"[OTP BALE] Successfully set code '{otp}' in cache for phone: {phone}")

    await update.message.reply_text(
        f"🔑 *کد ورود شما با موفقیت تولید شد:*\n\n"
        f"👑 `{otp}`\n\n"
        f"⚠️ *توجه مهم:* این کد فقط برای شماره موبایل **`{phone}`** معتبر است. "
        f"لطفاً در صفحه ورود تفکر، حتماً همین شماره موبایل **`{phone}`** را وارد کنید؛ "
        f"در غیر این صورت خطای منقضی شدن کد را دریافت خواهید کرد.",
        parse_mode="Markdown"
    )

def main():
    # خواندن توکن اختصاصی ربات OTP بله از متغیرهای محیطی یا تنظیمات
    bot_token = os.getenv("BALE_OTP_BOT_TOKEN") or getattr(settings, "BALE_BOT_TOKEN", None)
    if not bot_token:
        logger.error("BALE_OTP_BOT_TOKEN or BALE_BOT_TOKEN is not set in environment or Django settings!")
        return

    logger.info("Starting Bale OTP Bot...")
    app = (
        ApplicationBuilder()
        .token(bot_token)
        .base_url("https://tapi.bale.ai/bot")
        .base_file_url("https://tapi.bale.ai/file/bot")
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # پیام‌های عمومی دیگر را با درخواست شماره ریپلای کن
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    app.run_polling(poll_interval=2.0)

if __name__ == "__main__":
    main()
