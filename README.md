# 📘 Tafakor – README (Development & Deployment Guide)

یک پلتفرم یادداشت‌برداری مبتنی بر وب با **Vue 3** در فرانت‌اند و **Django** در بک‌اند، همراه با همگام‌سازی خودکار در پیام‌رسان‌های تلگرام و بله از طریق ربات‌های اختصاصی.

این راهنما تمام مراحل اجرا، توسعه، تست و استقرار پروژه را با استفاده از Docker پوشش می‌دهد.

---

# 📑 فهرست مطالب

- [راه‌اندازی روی سرور (Production Deployment)](#1-راهاندازی-روی-سرور-production-deployment)
- [اجرای محلی کل پروژه (Local Full-Stack Development)](#2-اجرای-محلی-کل-پروژه-local-fullstack-development)
- [اجرای هر بخش به‌طور مجزا (Running Individual Services)](#3-اجرای-هر-بخش-بهطور-مجزا-running-individual-services)
- [توضیحات داکر پروژه (Docker Architecture)](#4-توضیحات-داکر-پروژه-docker-architecture)
- [روش توسعه و تست با داکر (Development & Testing Workflow)](#5-روش-توسعه-و-تست-با-داکر-development--testing-workflow)
- [کلیدواژه‌ها / Keywords](#6-کلیدواژهها--keywords)

---

# 1. راه‌اندازی روی سرور (Production Deployment)

برای استقرار نهایی روی یک سرور لینوکسی با Docker.

## پیش‌نیازها

- Docker Engine `20.10+`
- Docker Compose v2
- دسترسی به اینترنت یا تنظیم mirror برای pull ایمیج‌ها

---

## مراحل

### 1. کلون کردن پروژه

```bash
git clone https://your-repo-url.git tafakor
cd tafakor
```

---

### 2. تنظیم فایل `.env` سراسری

تمام تنظیمات پروژه (شامل دیتابیس، ربات‌ها، کاوه‌نگار و ماژول پروکسی) در فایل واحد [`.env`](file:///f:/tafakor/.env) در ریشه پروژه متمرکز شده است. 

کافیست فایل نمونه را ویرایش کرده و متغیرهای آن را بر اساس سناریوی خود تنظیم کنید (برای اجرای داکر روی سرور ادمین، مقدار `DB_HOST=db` را فعال کنید).

---

### 3. ساخت و اجرای سرویس‌ها

برای اجرای معمولی پروژه (بک‌اند، فرانت‌اند، دیتابیس و ربات بله):
```bash
docker compose up -d --build
```

**فعال‌سازی درگاه تلگرام (بای‌پس فیلترینگ):**
اگر پروژه را روی سرور مستقر در ایران اجرا می‌کنید و نیاز به پروکسی تلگرام دارید، کافیست پروژه را همراه با پروفایل `proxy` اجرا کنید تا کانتینر پروکسی تلگرام نیز بالا بیاید:
```bash
docker compose --profile proxy up -d --build
```

---

### 4. بررسی وضعیت سرویس‌ها

```bash
docker compose ps
docker compose logs -f
```

---

### 5. دسترسی به برنامه

- برنامه اصلی:

```text
http://<server-ip>:8085 (یا پورت تنظیمی در FRONTEND_PORT)
```

- پنل ادمین:

```text
http://<server-ip>:8085/admin/ (یا پورت تنظیمی در FRONTEND_PORT/admin/)
```

ساخت ابرکاربر:

```bash
docker exec -it tafakor_backend python manage.py createsuperuser
```

---

### 6. تغییر پورت پیش‌فرض فرانت‌اند روی سرور

پورت فرانت‌اند روی سرور به صورت پیش‌فرض روی `8085` تنظیم شده است تا تداخلی ایجاد نشود. برای تغییر آن، کافیست مقدار متغیر `FRONTEND_PORT` را در فایل `.env.docker` به پورت دلخواه خود تغییر دهید و مجدداً پروژه را اجرا کنید.

---

# 2. اجرای محلی کل پروژه (Local Full-Stack Development)

برای توسعه و تست روی Windows / macOS / Linux با قابلیت Hot Reload.

---

## تفاوت با Production

در محیط توسعه:

- Django با `runserver` اجرا می‌شود.
- فرانت‌اند با `Vite Dev Server` اجرا می‌شود.
- کدها به‌صورت زنده داخل کانتینر mount می‌شوند.
- سرویس ربات‌ها به صورت خودکار اجرا می‌شود (تنظیم توکن‌ها و فعال‌سازی از طریق فایل `.env`).

---

## پیش‌نیازها

- Docker Desktop یا Docker Engine + Compose v2
- وجود فایل `docker-compose.override.yml`

---

## مراحل

### 1. اطمینان از وجود فایل Override

فایل زیر باید کنار `docker-compose.yml` قرار داشته باشد:

```text
docker-compose.override.yml
```

این فایل تنظیمات مخصوص توسعه را اعمال می‌کند.

---

### 2. اجرای پروژه

```bash
docker-compose up -d
```

> نیازی به `--env-file` نیست؛ متغیرهای پیش‌فرض داخل override تعریف شده‌اند.

---

### 3. دسترسی به سرویس‌ها

#### Frontend

```text
http://localhost:8080 (یا پورت تنظیمی در FRONTEND_DEV_PORT)
```

یا:

```text
http://localhost:5173 (دسترسی مستقیم به Vite Dev Server)
```

#### Backend API

```text
http://localhost:8000/api/
```

#### Database

```text
localhost:5433
```

---

### 4. وضعیت کانتینر ربات‌ها (Bale & Telegram)

ربات‌ها اکنون به صورت خودکار با دستور `docker-compose up -d` اجرا می‌شوند.
- برای فعال کردن ربات تلگرام، متغیر `ENABLE_TELEGRAM=true` را در فایل `.env` قرار دهید.
- برای بات بله، از قبل توکن تستی در فایل `docker-compose.override.yml` قرار داده شده و فعال است.

---

### 5. اعمال تغییرات

هر تغییری در پوشه‌های:

```text
backend/
frontend/
```

به‌صورت خودکار reload می‌شود و نیازی به build مجدد نیست.

---

# 3. اجرای هر بخش به‌طور مجزا (Running Individual Services)

| سرویس | دستور | توضیح |
|---|---|---|
| فقط بک‌اند + دیتابیس | `docker-compose up -d backend` | دیتابیس هم اجرا می‌شود |
| فقط فرانت + بک‌اند + دیتابیس | `docker-compose up -d frontend` | به دلیل وابستگی backend و db اجرا می‌شوند |
| فقط ربات | `docker-compose --profile bot up -d bot_runner` | نیازمند profile |
| فقط دیتابیس | `docker-compose up -d db` | مناسب تست SQL |
| اجرای مستقل سرویس | `docker-compose run --service-ports --no-deps backend` | بدون اجرای وابستگی‌ها |

---

# 4. توضیحات داکر پروژه (Docker Architecture)

پروژه توسط Docker Compose مدیریت می‌شود و شامل چهار سرویس اصلی است.

---

## فایل‌های کلیدی

### `docker-compose.yml`

تنظیمات Production پروژه.

---

### `docker-compose.override.yml`

تنظیمات مخصوص توسعه:

- volumes
- command
- port mapping
- hot reload

> این فایل روی سرور Production وجود ندارد.

---

## سرویس‌ها

| سرویس | Dockerfile / Image | نقش |
|---|---|---|
| `db` | `postgres:15` | پایگاه داده PostgreSQL |
| `backend` | `backend/Dockerfile` | بک‌اند جنگو (Django API Server) |
| `frontend` | `frontend/Dockerfile` | فرانت‌اند ویو (Vue + Nginx / Vite) |
| `bot_runner` | `bot_runner/Dockerfile` | ربات بله و تلگرام |
| `telegram_proxy` | `telegram_proxy/Dockerfile` | دور زدن فیلترینگ تلگرام (پروکسی رله) |

---

## شبکه و Volumes

### Network

```text
tafakor_net
```

از نوع `bridge` و برای ارتباط داخلی سرویس‌ها.

---

### Volumes

| Volume | کاربرد |
|---|---|
| `postgres_data` | نگهداری دائمی دیتابیس |
| `static_volume` | اشتراک فایل‌های static بین backend و frontend |

---

# 5. روش توسعه و تست با داکر (Development & Testing Workflow)

هدف این فرآیند، یکسان‌سازی محیط توسعه بین اعضای تیم و کاهش خطاهای محیطی است.

---

## 5.1 شروع یک فیچر جدید

1. ایجاد branch جدید از شاخه اصلی
2. اجرای پروژه:

```bash
docker compose up -d
```

3. توسعه کدها با Hot Reload
4. در صورت نیاز به فعال‌سازی پروکسی بای‌پس تلگرام جهت تست محلی ربات تلگرام:

```bash
docker compose --profile proxy up -d
```

---

## 5.2 تست تغییرات

### Backend

```bash
docker compose exec backend python manage.py test
```

یا ارسال درخواست به:

```text
http://localhost:8000/api/
```

---

### Frontend

تغییرات در:

```text
frontend/src/
```

بلافاصله در مرورگر قابل مشاهده‌اند.

---

### Bot

ارسال دستور زیر به ربات در بله:

```text
/start
```

---

### Database

```bash
docker-compose exec db psql -U postgres -d tafakor
```

---

## 5.3 بازسازی ایمیج‌ها

در صورت تغییر Dockerfile یا وابستگی‌ها:

```bash
docker compose build --no-cache <service_name>
```

---

## 5.4 دیباگ

### مشاهده لاگ‌ها

```bash
docker compose logs -f <service_name>
```

### ورود به کانتینر

```bash
docker exec -it tafakor_backend bash
```

یا:

```bash
docker exec -it tafakor_backend sh
```

---

# 6. کلیدواژه‌ها / Keywords

```text
docker-compose up
docker-compose override
local development

tafakor production deploy
tafakor docker

بله ربات
bale bot
python-telegram-bot base_url

hot reload django
vite hmr

docker individual service
run single container

tafakor environment variables
tafakor unified .env
telegram_proxy bypass
telegram bypass relay

postgres docker volume
static files nginx

runserver vs gunicorn
debug mode
```

---

# پرسش‌ها یا پیشنهادها

در صورت بروز مشکل یا نیاز به تغییر در مستندات:

- یک Issue در مخزن پروژه ثبت کنید.
- یا با تیم توسعه تماس بگیرید.