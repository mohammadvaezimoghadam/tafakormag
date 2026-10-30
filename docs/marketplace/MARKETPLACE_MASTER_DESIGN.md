# 🏛️ سند جامع معماری، طراحی دیتابیس و الزامات بازارچه و اهدا تفاخر
> **Tafakor Marketplace & Donation Platform — Master Architecture, DB Schema & Design Rules**  
> *نسخه: ۱.۰.۰ | تاریخ آخرین بروزرسانی: ۲۶ اکتبر ۲۰۲۶*

---

## فهرست مطالب
1. [معماری سیستم و چرایی تصمیمات فنی (ADR)](#۱-معماری-سیستم-و-چرایی-تصمیمات-فنی-adr)
2. [تشریح جریان‌های کاری سیستم (Business Workflows)](#۲-تشریح-جریانهای-کاری-سیستم-business-workflows)
3. [چالش‌ها، گلوگاه‌ها و اصول حیاتی توسعه‌پذیری](#۳-چالشها-گلوگاهها-و-اصول-حیاتی-توسعهپذیری)
4. [طراحی کامل دیتابیس (DBML استاندارد dbdiagram.io)](#۴-طراحی-کامل-دیتابیس-dbml-استاندارد-dbdiagramio)
5. [جدول تصمیمات، وضعیت‌ها و توسعه‌های آتی](#۵-جدول-تصمیمات-وضعیتها-و-توسعههای-آتی)

---

## ۱. معماری سیستم و چرایی تصمیمات فنی (ADR)

### ۱.۱. چرا مانند `bot_runner` سرویس جداگانه (Microservice) نشد؟
* **سرویس `bot_runner`:** یک پروسس غیرهمگام (Async Event Loop) برای ارتباطات مداوم وب‌سوکت و لانگ‌پولینگ با پیام‌رسان‌های بله و تلگرام است، دیتابیس تراکنشی ندارد و صرفاً یک پروکسی است.
* **بازارچه و فروشگاه:** شدیداً داده‌محور و وابسته به تراکنش‌های ACID بانکی است. روابط مستقیم و تنگاتنگ با جدول کاربران (`User`)، آدرس‌ها، آپلود فایل‌ها و حسابداری دارد. جدا کردن آن در قالب میکروسرویس مستقل باعث هزینه‌های سنگین همگام‌سازی احراز هویت (Auth Sync)، تراکنش‌های توزیع‌شده (2PC / Sagas) و از دست رفتن قابلیت‌های ORM جنگو می‌شد.

### ۱.۲. مدل انتخابی: معماری هیبریدی (Hybrid Plugin Architecture)
* **هسته تفاخر (Core Platform):**
  * `apps.accounts`: نگهداری اطلاعات هویتی و جدول آدرس‌های پستی کاربران (`addresses`) جهت استفاده اشتراکی در کل سیستم.
  * `apps.payments`: موتور و زیرساخت متمرکز درگاه‌های بانکی (زرین‌پال، شاپرک و ...) جهت سرویس‌دهی مشترک به کمپین‌های نیکوکاری (`apps.donations`) و بازارچه.
* **پلاگین رسمی تفاخر (`backend/plugins/marketplace`):**
  * تمامی جداول و فرآیندهای تخصصی بازارچه، کالاها، سفارشات، سبد خرید، سیستم اهدا و فایل‌های دیجیتال در قالب پلاگین رسمی ثبت در `INSTALLED_TAFAKOR_PLUGINS`.
  * فرانت‌اند به صورت Mini-App اختصاصی با قابلیت پیوند با تاپیک‌ها و پست‌ها از طریق Action کامپوزر.

---

## ۲. تشریح جریان‌های کاری سیستم (Business Workflows)

### ۲.۱. جریان اهدا (C2C Donation Flow)
1. اهداکننده کالا را با نوع `deal_type = donation` و قیمت ۰ ثبت می‌کند.
2. متقاضیان پیام درخواست ثبت می‌کنند (`donation_requests`).
3. اهداکننده یکی از درخواست‌ها را می‌پذیرد (`accepted`).
4. رکورد قطعی `donations` ساخته می‌شود، سایر درخواست‌ها رد می‌شوند و وضعیت کالا به `reserved` یا `completed` تغییر می‌کند.
5. **اگر فیزیکی باشد:** آدرس گیرنده ثبت شده، تعیین می‌شود هزینه ارسال با کیست (`shipping_payer`) و کد رهگیری پست درج می‌شود.
6. **اگر دیجیتال باشد:** رکورد دسترسی در `digital_accesses` ایجاد شده و فایل در بخش دانلودهای گیرنده قرار می‌گیرد.

### ۲.۲. جریان خرید با سیستم امانی (Order & Escrow Flow)
1. خریدار کالا را به سبد خرید اضافه می‌کند.
2. در لحظه ثبت سفارش، کالا به مدت ۱۵ دقیقه رزرو می‌شود (`reserved_until`).
3. خریدار از طریق درگاه پرداخت متمرکز هزینه را واریز می‌کند.
4. پس از تایید تراکنش، سفارش `paid` می‌شود و برای هر فروشنده یک بسته ارسالی (`order_shipments`) شکل می‌گیرد.
5. مبلغ به صورت امانت (Escrow) در وضعیت `held` نزد پلتفرم باقی می‌ماند (`seller_settlements`).
6. پس از ارسال کالا توسط فروشنده و تایید دریافت توسط خریدار (یا گذشت مهلت قانونی)، وجه به کیف پول فروشنده آزاد می‌شود (`approved` / `settled`).

---

## ۳. چالش‌ها، گلوگاه‌ها و اصول حیاتی توسعه‌پذیری

این نکات باید در تمامی مراحل طراحی مدل‌ها و پیاده‌سازی سرویس‌ها دقیقاً رعایت شوند:

| # | عنوان چالش / اصل | شرح ریسک در صورت عدم رعایت | راهکار قطعی و الزامی در طراحی |
|---|---|---|---|
| **۱** | **سبد خرید چند فروشنده‌ای** | خریدار از ۲ فروشنده در ۲ شهر خرید می‌کند؛ با یک کد رهگیری و یک هزینه پست نمی‌توان سفارش را مدیریت کرد. | شکستن سفارش به زیربسته‌های ارسال به تفکیک فروشنده در جدول `order_shipments`. |
| **۲** | **همزمانی خرید کالای تکی (Race Condition)** | دو نفر همزمان به درگاه بروند و هر دو پول پرداخت کنند در حالی که کالا ۱ عدد است. | استفاده از قفل موقت زمان‌دار (`reserved_until`) به مدت ۱۵ دقیقه هنگام رفتن به درگاه. |
| **۳** | **موجودی و تیراژ (Inventory)** | ناتوانی در فروش فایل دیجیتال به تعداد نامحدود یا فروش کالاهایی با تیراژ بیش از ۱ عدد. | وجود فیلد `stock` در کالا و فیلد `quantity` در اقلام سفارش. |
| **۴** | **سیستم امانی تسویه (Escrow)** | واریز مستقیم به فروشنده قبل از رسیدن کالا باعث کلاهبرداری و بی اعتمادی می‌شود. | ایجاد جدول `seller_settlements` و آزادسازی وجه پس از تایید دریافت خریدار. |
| **۵** | **امنیت فایل دیجیتال** | لو رفتن لینک مستقیم فایل و انتشار عمومی بدون پرداخت. | ذخیره کلید امن (`digital_file_key`)، دانلود فقط از طریق API با لینک موقت امضاشده (Presigned URL) و سقف دانلود. |
| **۶** | **اعتبارسنجی نظرات (Verified Reviews)** | ثبت نظر و امتیاز تخریبی توسط رقبای فروشنده بدون خرید کالا. | اجباری بودن انتساب نظر به `order_id` یا `donation_id`. |
| **۷** | **نرمال‌سازی موقعیت جغرافیایی** | ذخیره متن خام شهر و استان باعث غلط‌های املایی و غیرممکن شدن فیلتر استانی می‌شود. | استفاده از جداول استاندارد `provinces` و `cities`. |
| **۸** | **کاتالوگ استاندارد کتاب‌ها** | تکرار اطلاعات شابک، ناشر و نویسنده در دیتابیس و جستجوی سخت در JSON. | ایجاد جدول اختصاصی `book_details` با رابطه یک‌به‌یک برای کالاهای دسته‌بندی کتاب. |
| **۹** | **حذف کاربر (Referential Integrity)** | در صورت حذف کاربر، سفارش‌ها و رکوردهای مالی نباید پاک شوند. | استفاده از `on_delete=models.PROTECT` و پیاده‌سازی حذف نرم (Soft Delete). |
| **۱۰**| **پیوند با تاپیک‌های تفاخر** | جدا افتادن بازارچه از بستر گفتگو و اندیشه تفاخر. | فیلد اختیاری `topic_id` در جدول کالا برای نمایش اقلام در صفحات تاپیک‌ها. |

---

## ۴. طراحی کامل دیتابیس (DBML استاندارد dbdiagram.io)

کد زیر به صورت کامل و آماده برای کپی در [dbdiagram.io](https://dbdiagram.io) آماده شده است. تمامی جدول‌ها از جمله `users` به درستی در ابتدا تعریف شده‌اند تا هیچ خطایی رخ ندهد:

```dbml
// ==========================================
// 1. کاربران سیستم (Tafakor Core Users)
// ==========================================
Table users {
  id integer [pk, increment]
  phone varchar(11) [unique, not null]
  first_name varchar(100)
  last_name varchar(100)
  profile_image varchar
  is_active boolean [default: true]
  is_verified boolean [default: false]
  deleted_at timestamp [null]
  created_at timestamp [default: `now()`]
  updated_at timestamp
}

Table topics {
  id integer [pk, increment]
  title varchar(255) [not null]
  slug varchar(255) [unique, not null]
  is_active boolean [default: true]
}

// ==========================================
// 2. موقعیت مکانی و حساب‌های مالی
// ==========================================
Table provinces {
  id integer [pk, increment]
  name varchar(100) [not null]
}

Table cities {
  id integer [pk, increment]
  province_id integer [ref: > provinces.id, not null]
  name varchar(100) [not null]
}

Table addresses {
  id integer [pk, increment]
  user_id integer [ref: > users.id, not null]
  title varchar(50)
  receiver_name varchar(100) [not null]
  receiver_phone varchar(15) [not null]
  city_id integer [ref: > cities.id, not null]
  postal_address text [not null]
  postal_code varchar(10) [not null]
  is_default boolean [default: false]
  deleted_at timestamp [null]
  created_at timestamp [default: `now()`]
}

Table seller_bank_accounts {
  id integer [pk, increment]
  user_id integer [ref: > users.id, not null]
  bank_name varchar(100) [not null]
  account_holder_name varchar(150) [not null]
  iban varchar(34) [unique, not null]           // شماره شبا
  is_verified boolean [default: false]          // وضعیت تایید حساب بانکی
  is_default boolean [default: true]
  created_at timestamp [default: `now()`]
}

// ==========================================
// 3. دسته‌بندی و کالاها (Items & Inventory)
// ==========================================
Table categories {
  id integer [pk, increment]
  name varchar(100) [not null]
  slug varchar(100) [unique, not null]
  parent_id integer [ref: > categories.id]
  icon varchar
  is_active boolean [default: true]
  order integer [default: 0]
}

Table items {
  id integer [pk, increment]
  seller_id integer [ref: > users.id, not null]
  category_id integer [ref: > categories.id, not null]
  topic_id integer [ref: > topics.id, null]      // پیوند با تاپیک‌های تفاخر
  
  title varchar(255) [not null]
  slug varchar(255) [unique]
  description text
  
  deal_type varchar(20) [not null]               // donation | sale
  delivery_type varchar(20) [not null]           // physical | digital
  
  price decimal(14, 0) [default: 0]              // قیمت اصلی کالا
  discount_price decimal(14, 0) [null]           // قیمت تخفیف خورده مستقیم
  discount_ends_at timestamp [null]              // تاریخ پایان تخفیف کالا
  
  stock integer [default: 1]                     // تعداد موجودی
  is_unlimited_stock boolean [default: false]    // برای فایل‌های دانلودی
  
  // مشخصات فیزیکی
  condition varchar(30)                          // new | like_new | used | damaged
  city_id integer [ref: > cities.id]             // موقعیت فیزیکی کالا
  weight_grams integer [default: 0]              // وزن برای محاسبه کرایه پست
  
  // مشخصات دیجیتال امن
  digital_file_key varchar                       // کلید ذخیره‌سازی امن فایل
  file_format varchar(20)
  file_size_mb decimal(8, 2)
  
  // وضعیت و قفل همزمانی خرید
  status varchar(30) [default: 'draft']          // draft | available | reserved | completed | archived
  reserved_until timestamp [null]                // زمان پایان رزرو درگاه
  
  views_count integer [default: 0]
  is_featured boolean [default: false]
  
  deleted_at timestamp [null]                    // حذف نرم
  created_at timestamp [default: `now()`]
  updated_at timestamp
}

Table item_images {
  id integer [pk, increment]
  item_id integer [ref: > items.id, not null]
  image_url varchar [not null]
  is_cover boolean [default: false]
  sort_order integer [default: 0]
}

Table book_details {
  item_id integer [pk, ref: - items.id]          // ارتباط یک‌به‌یک با کالا (فقط کتاب)
  isbn varchar(20) [null]                        // شابک
  author varchar(150) [not null]                 // نویسنده
  translator varchar(150)                        // مترجم
  publisher varchar(150)                         // ناشر
  publication_year integer                       // سال چاپ
  pages_count integer                            // تعداد صفحات
}

Table item_attributes {
  id integer [pk, increment]
  item_id integer [ref: > items.id, not null]
  attribute_key varchar(50) [not null]           // مثلا: technique, dimensions, material, format
  attribute_value text [not null]                // مثلا: رنگ روغن، ۵۰x۷۰، چوب گردو، PDF
  created_at timestamp [default: `now()`]
  
  indexes {
    (item_id, attribute_key) [unique]
  }
}

Table wishlists {
  id integer [pk, increment]
  user_id integer [ref: > users.id, not null]
  item_id integer [ref: > items.id, not null]
  created_at timestamp [default: `now()`]
  
  indexes {
    (user_id, item_id) [unique]
  }
}

// ==========================================
// 4. سبد خرید موقت (Shopping Cart)
// ==========================================
Table carts {
  id integer [pk, increment]
  user_id integer [ref: > users.id, not null]
  created_at timestamp [default: `now()`]
  updated_at timestamp
}

Table cart_items {
  id integer [pk, increment]
  cart_id integer [ref: > carts.id, not null]
  item_id integer [ref: > items.id, not null]
  quantity integer [default: 1]
  created_at timestamp [default: `now()`]
  
  indexes {
    (cart_id, item_id) [unique]
  }
}

// ==========================================
// 5. کدهای تخفیف و کوپن‌ها (Coupons)
// ==========================================
Table coupons {
  id integer [pk, increment]
  code varchar(50) [unique, not null]
  title varchar(150)
  discount_type varchar(20) [not null]           // percentage | fixed_amount
  discount_value decimal(14, 0) [not null]
  max_discount_amount decimal(14, 0) [null]
  min_order_amount decimal(14, 0) [default: 0]
  seller_id integer [ref: > users.id, null]
  discount_bearer varchar(20) [default: 'platform'] // platform | seller
  usage_limit integer [null]
  user_usage_limit integer [default: 1]
  used_count integer [default: 0]
  valid_from timestamp [default: `now()`]
  valid_until timestamp [null]
  is_active boolean [default: true]
  created_at timestamp [default: `now()`]
}

// ==========================================
// 6. سیستم اهدا (Donation System)
// ==========================================
Table donation_requests {
  id integer [pk, increment]
  item_id integer [ref: > items.id, not null]
  requester_id integer [ref: > users.id, not null]
  message text
  status varchar(20) [default: 'pending']        // pending | accepted | rejected | cancelled
  created_at timestamp [default: `now()`]
  
  indexes {
    (item_id, requester_id) [unique]
  }
}

Table donations {
  id integer [pk, increment]
  item_id integer [ref: > items.id, not null]
  donor_id integer [ref: > users.id, not null]
  recipient_id integer [ref: > users.id, not null]
  donation_request_id integer [ref: > donation_requests.id]
  
  status varchar(30) [default: 'accepted']       // accepted | shipped | delivered | cancelled
  shipping_address_id integer [ref: > addresses.id]
  shipping_payer varchar(20)                     // donor | recipient
  tracking_code varchar(100)
  
  accepted_at timestamp [default: `now()`]
  shipped_at timestamp
  delivered_at timestamp
}

// ==========================================
// 7. سیستم سفارشات رسمی (Orders & Shipments)
// ==========================================
Table orders {
  id integer [pk, increment]
  buyer_id integer [ref: > users.id, not null]
  order_number varchar(50) [unique, not null]
  coupon_id integer [ref: > coupons.id, null]
  
  total_items_amount decimal(14, 0) [not null]
  total_shipping_cost decimal(14, 0) [default: 0]
  discount_amount decimal(14, 0) [default: 0]
  payable_amount decimal(14, 0) [not null]
  
  status varchar(30) [default: 'pending']        // pending | paid | processing | completed | cancelled
  payment_status varchar(30) [default: 'unpaid'] // unpaid | paid | refunded
  
  shipping_address_id integer [ref: > addresses.id]
  deleted_at timestamp [null]
  created_at timestamp [default: `now()`]
  updated_at timestamp
}

Table order_shipments {
  id integer [pk, increment]
  order_id integer [ref: > orders.id, not null]
  seller_id integer [ref: > users.id, not null]
  
  shipping_cost decimal(14, 0) [default: 0]
  shipping_method varchar(50)                    // پست پیشتاز | تیپاکس | پیک
  tracking_code varchar(100)
  
  status varchar(30) [default: 'processing']     // processing | shipped | delivered | dispute
  shipped_at timestamp
  delivered_at timestamp
}

Table order_items {
  id integer [pk, increment]
  order_id integer [ref: > orders.id, not null]  // لینک مستقیم برای گزارش‌گیری سریع
  shipment_id integer [ref: > order_shipments.id, not null]
  item_id integer [ref: > items.id, not null]
  quantity integer [default: 1]
  unit_price decimal(14, 0) [not null]
  discount_amount decimal(14, 0) [default: 0]
}

Table coupon_usages {
  id integer [pk, increment]
  coupon_id integer [ref: > coupons.id, not null]
  user_id integer [ref: > users.id, not null]
  order_id integer [ref: > orders.id, not null]
  discount_applied decimal(14, 0) [not null]
  created_at timestamp [default: `now()`]
  
  indexes {
    (coupon_id, user_id, order_id) [unique]
  }
}

// ==========================================
// 8. پرداخت‌ها و تسویه‌حساب امانی (Escrow)
// ==========================================
Table payments {
  id integer [pk, increment]
  order_id integer [ref: > orders.id, not null]
  amount decimal(14, 0) [not null]
  gateway varchar(50)                            // zarinpal | idpay | saman
  authority varchar(100) [unique]                // شناسه درخواست درگاه
  tracking_code varchar(100)                     // شماره پیگیری بانکی
  status varchar(30) [default: 'pending']        // pending | successful | failed
  raw_response json
  paid_at timestamp
  created_at timestamp [default: `now()`]
}

Table seller_settlements {
  id integer [pk, increment]
  seller_id integer [ref: > users.id, not null]
  shipment_id integer [ref: > order_shipments.id, not null]
  bank_account_id integer [ref: > seller_bank_accounts.id, not null] // ارجاع به حساب بانکی تایید شده
  
  gross_amount decimal(14, 0) [not null]         // کل مبلغ فروش بدون تخفیف
  platform_fee decimal(14, 0) [default: 0]       // کارمزد سایت
  seller_discount_share decimal(14, 0) [default: 0] // سهم تخفیف فروشنده
  net_amount decimal(14, 0) [not null]           // سهم خالص فروشنده
  
  status varchar(30) [default: 'held']           // held (امانت) | approved (تایید شده) | settled (تسویه شده)
  settled_at timestamp
}

// ==========================================
// 9. دسترسی به فایل‌های دیجیتال امن
// ==========================================
Table digital_accesses {
  id integer [pk, increment]
  user_id integer [ref: > users.id, not null]
  item_id integer [ref: > items.id, not null]
  granted_via varchar(20)                        // purchase | donation
  order_id integer [ref: > orders.id]
  donation_id integer [ref: > donations.id]
  
  download_count integer [default: 0]
  max_downloads integer [default: 5]             // سقف دفعات مجاز دانلود
  expires_at timestamp [null]                    // تاریخ انقضای دانلود
  last_downloaded_at timestamp
  created_at timestamp [default: `now()`]
  
  indexes {
    (user_id, item_id) [unique]
  }
}

// ==========================================
// 10. نظرات اعتبارسنجی شده (Verified Reviews)
// ==========================================
Table reviews {
  id integer [pk, increment]
  item_id integer [ref: > items.id, not null]
  reviewer_id integer [ref: > users.id, not null]
  order_id integer [ref: > orders.id]            // اثبات خرید
  donation_id integer [ref: > donations.id]      // اثبات اهدا
  rating integer [not null]                      // 1 تا 5
  comment text
  created_at timestamp [default: `now()`]
  
  indexes {
    (item_id, reviewer_id) [unique]
  }
}
```

---

## ۵. جدول تصمیمات، وضعیت‌ها و توسعه‌های آتی

| موضوع | تصمیم / وضعیت فعلی | برنامه آینده |
|---|---|---|
| **حذف کاربر ثبت‌کننده کالا** | `on_delete=models.PROTECT` در جنگو برای حفظ اسناد مالی و اهداها. | در صورت حذف کاربر، نام او به «کاربر غیرفعال» نمایش داده شده و حذف فیزیکی انجام نمی‌شود (Soft Delete). |
| **کاتالوگ کتاب‌ها** | جدول تکمیلی ۱ به ۱ `book_details` پیاده‌سازی شد. | در نسخه‌های بعدی، اتصال به وب‌سرویس خانه کتاب جهت پر شدن خودکار مشخصات با وارد کردن شابک. |
| **کیف پول داخلی** | تسویه‌حساب دوره‌ای بر اساس شبا (`seller_settlements`). | راه‌اندازی کیف پول اعتباری (`UserWallet`) جهت خرید بدون ورود هر باره به درگاه بانکی. |
| **سیستم داوری و حل اختلاف** | وضعیت `dispute` در `order_shipments` جهت ورود ادمین. | پنل داوری برای بازپس‌فرستادن کالا یا برگشت وجه به خریدار. |
