# 📘 راهنمای جامع تست‌های پلتفرم تفکر (Tafakor Testing Guide)

این سند برای درک سریع ساختار تست‌های پلتفرم تفکر، بخش‌های تحت پوشش و فرآیند اجرای آن‌ها تهیه شده است.

---

## 🏗️ ساختار کلی تست‌ها (Test Structure)

تست‌های پروژه در سه بخش اصلی فرانت‌اند، بک‌اند و ربات‌رانر دسته‌بندی شده‌اند:

```
tafakor/
├── backend/
│   └── apps/
│       ├── accounts/tests.py          # تست‌های واحد احراز هویت و OTP
│       ├── donations/tests/           # تست‌های واحد مدل‌ها، سرویس‌ها و API اهدا
│       │   ├── test_models.py
│       │   ├── test_services.py
│       │   └── test_api.py
│       └── notes/tests.py             # تست‌های واحد مدل‌های یادداشت‌ها، تاپیک و ایمپورت تلگرام
├── frontend/
│   └── src/
│       └── lib/utils.test.js          # تست‌های واحد توابع فرانت‌اند (Node Native Test)
└── tests/
    ├── e2e/
    │   └── test_critical_path.py      # تست‌های سرتاسری مرورگر (Playwright) شامل لاگین، تاپیک، اهدا و ربات
    └── integration/
        ├── test_donations_api.py      # تست یکپارچه‌سازی وب‌سرویس‌های اهدا، مجوزها، تسویه و پروفایل
        ├── test_notes_api.py          # تست وب‌سرویس‌های مدیریت یادداشت‌ها و تاپیک‌ها
        ├── test_bot_api.py            # تست وب‌سرویس‌های سمت ربات و اتصال چت‌ها
        ├── test_bot_runner.py         # تست لوپ پردازش صف تسک‌های ربات
        ├── test_bot_handlers.py       # تست موک هندلرهای ربات (تلگرام/بله)
        └── test_telegram_proxy.py     # تست شبیه‌ساز پروکسی ضد فیلتر تلگرام
```

---

## 🔄 توضیح فرآیند تست بخش‌ها به ترتیب (Testing Process)

### ۱. تست‌های واحد فرانت‌اند (Frontend Unit Tests)
* **بخش تحت پوشش:** توابع کمکی قالب‌بندی و کامپوننت‌های فرانت‌اند.
* **فایل تست:** [utils.test.js](file:///f:/AVA/tafakor/frontend/src/lib/utils.test.js)
* **فرآیند تست:** 
  1. بررسی ترکیب درست کلاس‌های CSS توسط تابع `cn` بر اساس اصول Tailwind و ادغام کلاس‌های متعارض.
  2. بررسی پشتیبانی از آرایه‌ها و آبجکت‌های شرطی.

### ۲. تست‌های واحد مدل‌ها و سرویس‌های بک‌اند (Backend Django Unit Tests)
* **بخش تحت پوشش:** صحت عملکرد پایگاه‌داده و اعتبارسنجی مقادیر فیلدهای جنگو.
* **فایل‌های تست:**
  * [tests.py (Accounts)](file:///f:/AVA/tafakor/backend/apps/accounts/tests.py): اعتبارسنجی ارسال OTP با کاوه‌نگار، تست انقضای کد تایید، و منطق سوئیچ خودکار به ربات بله (Fallback) در صورت خرابی سامانه پیامکی.
  * [tests.py (Notes)](file:///f:/AVA/tafakor/backend/apps/notes/tests.py): صحت‌سنجی روابط دیتابیس مدل‌های تاپیک، پست، کامنت و ری‌اکشن به همراه تست قید یکتا بودن واکنش کاربر، مدیریت ادمین‌ها و سرویس درون‌ریزی تلگرام (JSON/ZIP).
  * [apps/donations/tests/](file:///f:/AVA/tafakor/backend/apps/donations/tests/): تست‌های اتمیک مدل‌های پویش اهدا (`DonationCampaign`)، اعتبارسنجی حداقل مبالغ، تسویه همزمان و بدون مسدودی (`idempotent settlement`)، شبیه‌سازی تراکنش‌های همزمان، و لاگ‌های شفافیت.

### ۳. تست‌های یکپارچه‌سازی وب‌سرویس‌ها (Integration API Tests)
* **بخش تحت پوشش:** اندپوینت‌های REST API بک‌اند پلتفرم و جریان‌های تبادل داده.
* **فایل‌های تست:**
  * [test_donations_api.py](file:///f:/AVA/tafakor/tests/integration/test_donations_api.py): شبیه‌سازی ایجاد پویش در تاپیک، فیلتر موضوعی دسته‌بندی‌ها، انحصار سخت‌گیرانه ویرایش و حذف پویش صرفاً به سازنده، فرآیند آغاز و تسویه پرداخت با بروزرسانی متریک‌ها، و همگام‌سازی فیلد `donations_count` در پروفایل کاربر.
  * [test_notes_api.py](file:///f:/AVA/tafakor/tests/integration/test_notes_api.py): شبیه‌سازی ارسال درخواست‌های HTTP جهت ساخت تاپیک (با عکس)، ارسال پست، مدیریت مجوزهای دسترسی فقط برای سازندگان و تایید ثبت خودکار کارهای پس‌زمینه ربات (`BotTask`).
  * [test_bot_api.py](file:///f:/AVA/tafakor/tests/integration/test_bot_api.py): بررسی ثبت چت‌آیدی کاربران و تایید اتصال توکن موقت ربات‌ها.

### ۴. تست‌های پردازش تسک‌ها و هندلرهای ربات (Bot Runner Integration)
* **بخش تحت پوشش:** ربات‌رانر و درگاه پیام‌رسان‌ها.
* **فایل‌های تست:**
  * [test_bot_runner.py](file:///f:/AVA/tafakor/tests/integration/test_bot_runner.py): اعتبارسنجی تبدیل کدهای Markdown به تگ‌های معتبر HTML پیام‌رسان‌ها، مدیریت کارهای پردازش صف و واکنش به خطاهای محدودیت نرخ ارسال تلگرام (Rate Limit 429).
  * [test_bot_handlers.py](file:///f:/AVA/tafakor/tests/integration/test_bot_handlers.py): شبیه‌سازی رویدادهای ورودی ربات (مانند ارسال دستور `/start` یا `/register` در گروه) بدون نیاز به اینترنت و سرورهای خارجی.
  * [test_telegram_proxy.py](file:///f:/AVA/tafakor/tests/integration/test_telegram_proxy.py): صحت‌سنجی رله شدن امن کدهای ارسالی از پروکسی محلی به سمت پروکسی گوگل (GAS).

### ۵. تست‌های سرتاسری مرورگر (E2E Browser Tests)
* **بخش تحت پوشش:** شبیه‌سازی دقیق رفتار واقعی کاربر در کلاینت و سرور با مرورگر Headless Chromium.
* **فایل تست:** [test_critical_path.py](file:///f:/AVA/tafakor/tests/e2e/test_critical_path.py)
* **فرآیند تست:**
  1. `test_critical_path_login_flow`: ورود با OTP از کش دیتابیس، ساخت تاپیک، ارسال پست، ارسال کامنت، اعتبارسنجی شمارنده‌ها و حذف پست.
  2. `test_donate_navigation_flow`: ناوبری به صفحه `/donate`، اعتبارسنجی چیپس‌های دسته‌بندی و تب «توسط من».
  3. `test_custom_bot_registration`: ورود و ثبت توکن اختصاصی ربات در تب اتصالات پروفایل و بررسی نمایش نام کاربری ربات.

---

## 🚀 نحوه اجرای تست‌ها (How to Run)

### ۱. اجرای تست‌های بک‌اند، یکپارچه‌سازی و E2E (داکر)
برای اجرای تمام تست‌های کانتینری به همراه گزارش درصد پوشش کد (Coverage Report):
```powershell
# در روت پروژه (ویندوز)
.\run-tests.ps1
```
*گزارش پوشش کدهای پایتون در پوشه `tests/results/coverage/index.html` ذخیره می‌شود.*

### ۲. اجرای تست‌های فرانت‌اند (محلی)
برای اجرای تست‌های واحد Vue.js:
```bash
# رفتن به پوشه فرانت‌اند
cd frontend
# اجرای تست‌ها
npm run test:unit
```
