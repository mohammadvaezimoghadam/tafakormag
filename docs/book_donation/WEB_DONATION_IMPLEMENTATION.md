# 🌐 مستند پیاده‌سازی اهدای کتاب در وب‌سایت (Vue 3 / Tafakor Web)
> **Web Implementation Specification: Book Donation & Circulation**  
> *پروژه وب: `frontend/src/` | وضعیت: کامپوننت‌های پایه آماده، نیازمند بخش گیرنده*

---

## ۱. وضعیت کامپوننت‌های موجود در وب

| کامپوننت | وضعیت | کارکرد |
|---|---|---|
| **[AddShelfBookDialog.vue](file:///d:/django/tafakormag_avapardaz/frontend/src/components/shelf/AddShelfBookDialog.vue)** | ✅ پیاده‌شده | فرم ساده‌شده ۴ فیلدی برای ثبت کتاب در قفسه. |
| **[MyBookshelfView.vue](file:///d:/django/tafakormag_avapardaz/frontend/src/components/shelf/MyBookshelfView.vue)** | ✅ پیاده‌شده | گرید ۳ ستونه، دکمه مشکی «اهدا»، نمایش موجودی. |
| **[DonateSpecificBookDialog.vue](file:///d:/django/tafakormag_avapardaz/frontend/src/components/shelf/DonateSpecificBookDialog.vue)** | ✅ پیاده‌شده | دیالوگ اختصاصی اهدا با انتخاب تعداد جلد و دکمه تایید. |
| **[PlatformHomeHub.vue](file:///d:/django/tafakormag_avapardaz/frontend/src/components/home/PlatformHomeHub.vue)** | ✅ پیاده‌شده | هاب اصلی با دکمه ثبت کتاب و اسلایدر کتاب‌ها با دکمه اهدا. |

---

## ۲. بخش‌های مورد نیاز در وب برای تکمیل سناریو

1. **کارت «هدایای در انتظار دریافت» (Incoming Pending Gifts Banner):**
   - در بالای صفحه قفسه کتاب گیرنده یا هوم، اگر هدیه‌ای در انتظار تایید وجود داشته باشد:
     - نمایش عکس جلد، نام کتاب، نام اهداکننده و تعداد جلد.
     - دو دکمه: **«کتاب را تحویل گرفتم»** (سبز/مشکی) و **«رد هدیه / من نگرفتم»** (خاکستری/قرمز).
2. **برچسب هدیه در کارت‌های قفسه گیرنده:**
   - کتاب‌هایی که از طریق هدیه وارد قفسه شده‌اند، زیر نام کتاب برچسب ظریف دارند:  
     `هدیه از طرف: [نام اهداکننده]`  
   - دکمه «اهدا» برای این کارت‌ها پنهان است.
3. **صفحه فرود اسکن بارکد در وب (`/b/:code`):**
   - اگر فردی بدون اپ فلاتر بارکد کتاب را با دوربین گوشی اسکن کرد یا لینک پیامک را باز کرد:
     - این صفحه وب باز می‌شود، کتاب را نشان می‌دهد و اگر کاربر لاگین نباشد، با ورود شماره تلفن و کد تایید یکبارمصرف (OTP)، دکمه «کتاب را تحویل گرفتم» را پیش روی او می‌گذارد.
