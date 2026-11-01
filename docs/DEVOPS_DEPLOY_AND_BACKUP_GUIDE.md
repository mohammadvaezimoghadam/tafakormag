# راهنمای جامع دواپس: پشتیبان‌گیری، بازیابی اضطراری و دیپلوی بدون قطعی
**پروژه پلتفرم تفکر (Tafakor Mag / Avapardaz)**  
**تهیه‌شده بر اساس استانداردهای مهندسی SRE / DevOps**  
**آخرین بروزرسانی:** آبان ۱۴۰۵ (نوامبر ۲۰۲۶)

---

## ۱. اصل طلایی: پایداری ۱۰۰٪ و ممنوعیت قطعی (Zero-Downtime)

> [!CAUTION]
> **قانون اول دواپس:** هیچ‌گاه برای اعمال تغییرات یا دیپلوی، دستور `docker compose down` را اجرا نکنید!
> خاموش کردن کل داکر باعث قطع شدن دیتابیس، ارور ۵۰۲ برای کاربران و شکست تراکنش‌های فعال می‌شود.

در معماری کانتینری تفکر:
- کدهای پایتون به صورت Volume به کانتینر متصل هستند؛ نیاز به بیلد مجدد ایمیج ندارند.
- دیتابیس PostgreSQL باید همیشه روشن و در حالت `healthy` بماند.
- تنها سرویسی که هنگام تغییرات UI نیاز به بیلد کانتینر دارد، کانتینر **فرانت‌اند (Vue)** است.

---

## ۲. مشخصات و متغیرهای محیط پروداکشن (Production Reference)

- **آی‌پی سرور پروداکشن:** `5.202.19.101`
- **کاربر سرور:** `testaminadhami`
- **مسیر پروژه روی سرور:** `/home/testaminadhami/tafakormag_avapardaz`
- **برنچ فعال دیپلوی:** `5.1-miniapp` (یا برنچ فعال هماهنگ‌شده)
- **پورت سرویس‌ها:**
  - پورت دسترسی Nginx و برنامه: `8085`
  - پورت لوکال بک‌اند داکر: `8000`
  - پورت دیتابیس: `5432`

---

## ۳. دستورالعمل پشتیبان‌گیری دیتابیس (Database Backup)

### ۳.۱. گرفتن بک‌آپ فشرده و زمان‌دار
```bash
mkdir -p ~/backups
docker exec -t tafakor_db pg_dump -U postgres tafakor | gzip > ~/backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### ۳.۲. اعتبارسنجی سلامت بک‌آپ (حیاتی!)
هیچ‌گاه به صرف ساخت فایل اعتماد نکنید. حجم فایل را بررسی کنید:
```bash
ls -lh ~/backups
```
- **حجم سالم:** معمولاً ده‌ها کیلوبایت تا چندین مگابایت (مثلاً `90K` به بالا).
- **هشدار فایل خراب (تله ۱۴۱ بایتی):** اگر فایل حدود ۱۴۰ تا ۲۰۰ بایت بود، یعنی دستور با خطا مواجه شده و gzip متن ارور لینوکس را ذخیره کرده است! با دستور زیر محتوای ارور را بخوانید:
  ```bash
  zcat ~/backups/backup_xxxx.sql.gz
  ```

---

## ۴. سناریوی بازیابی اضطراری در شرایط فاجعه (Disaster Recovery / Restore)

اگر دیتابیس دچار خرابی یا تداخل شد، این فرآیند دیتابیس را در کمتر از ۱۰ ثانیه دقیقاً به نسخه بک‌آپ بازمی‌گرداند:

```bash
# گام ۱: پاکسازی کامل اسکیما جهت رفع تداخل کلیدهای تکراری
docker exec -t tafakor_db psql -U postgres -d tafakor -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# گام ۲: تزریق مستقیم فایل بک‌آپ فشرده به دیتابیس
gunzip -c ~/backups/backup_YYYYMMDD_HHMMSS.sql.gz | docker exec -i tafakor_db psql -U postgres -d tafakor > /dev/null
```
*(نکته فنی: در دستور دوم حتماً از سوییچ `-i` برای تزریق استریم ورودی استفاده می‌شود).*

---

## ۵. چرخه استاندارد دیپلوی و آپدیت کد (Deployment Workflow)

### گام ۱: دریافت آخرین کدها از مخزن گیت
روی سرور پروداکشن:
```bash
cd /home/testaminadhami/tafakormag_avapardaz
git pull origin 5.1-miniapp
```

### گام ۲: اعمال مایگریشن‌های دیتابیس (بدون قطعی)
```bash
docker exec -t tafakor_backend python manage.py migrate
```

### گام ۳: نوسازی ورکر‌های پایتون (Graceful Reload)
برای اعمال تغییرات کدهای بک‌اند (بدون خاموش کردن داکر):
```bash
docker restart tafakor_backend
```

---

## ۶. راز بیلد فرانت‌اند و مدیریت تله‌ی `frontend/dist` (بسیار مهم)

در `frontend/Dockerfile` یک مکانیزم هوشمند بررسی فایل‌های از پیش ساخته‌شده تعبیه شده است:
```dockerfile
if [ -f "./dist/index.html" ]; then
    echo "=== [OFFLINE DEPLOY READY] Prebuilt dist/index.html found! Skipping npm install & build completely ==="
else
    # Building from source via npmmirror/npmjs
fi
```

### دو رویکرد برای دیپلوی فرانت‌اند:

#### رویکرد الف (پیشنهادی و فوق‌سریع - Fast Prebuilt Deploy):
1. روی سیستم توسعه‌دهنده (Local)، فرانت‌اند را با داکر یا npm بیلد کرده و خروجی را در پوشه `frontend/dist` قرار می‌دهید.
2. پوشه `frontend/dist` را کامیت و پوش می‌کنید (`git add frontend/dist -f && git commit -m "build: update dist"`).
3. روی سرور فقط کافیست دستورات زیر را اجرا کنید (دیپلوی در کمتر از ۵ ثانیه بدون دانلود حتی ۱ بایت از npm!):
   ```bash
   git pull origin 5.1-miniapp
   docker compose build frontend
   docker compose up -d frontend
   ```

#### رویکرد ب (بیلد کامل از سورس روی سرور - Clean Build from Source):
اگر نمی‌خواهید `dist` را از لوکال پوش کنید و می‌خواهید سرور خودش از سورس کامپایل کند:
> [!WARNING]
> حتماً باید قبل از بیلد، پوشه قدیمی `dist` را حذف کنید، وگرنه داکر از همان فایل‌های قدیمی استفاده می‌کند و تغییرات جدید شما هرگز دیده نخواهد شد!
```bash
# ۱. حذف بیلد قبلی
rm -rf frontend/dist

# ۲. بیلد از سورس و جایگزینی کانتینر
docker compose build frontend
docker compose up -d frontend
```

---

## ۷. تست دود و راستی‌آزمایی (Smoke Test)

پس از هر دیپلوی، سلامت سرویس‌ها را با دستورات زیر بسنجید:
```bash
# بررسی سرویس پست‌ها و فیلتر قرآنی
curl -s "http://localhost:8085/api/notes/?ayah=1:1" | head -n 10

# بررسی ریسپانس کد صفحه اصلی وب
curl -I http://localhost:8085/

# مشاهده وضعیت کانتینرها
docker compose ps
```

---

## ۸. رفع کش مرورگر کلاینت (Hard Refresh)
پس از بروزرسانی فرانت‌اند، کلاینت‌ها برای دریافت فایل‌های جدید Vite باید کش مرورگر را خالی کنند:
- ویندوز / لینوکس: `Ctrl + F5` یا `Ctrl + Shift + R`
- مک: `Cmd + Shift + R`


