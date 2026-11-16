# 📖 سند معماری و طراحی سامانه انبار و اهدای کتاب پلتفرم تفکر
> **Tafakor Book Inventory, Donation & Circulation Master Architecture**  
> *تاریخ نگارش: ۲۵ آبان ۱۴۰۵ (16 Nov 2026) | نسخه: ۲.۰ (معماری اهدای مستقیم سازمانی تفکر)*

---

## ۱. بیانیه چشم‌انداز (Vision Statement)

پلتفرم تفکر رسالت توزیع و اهدای متمرکز کتاب به جامعه مخاطبان و کاربران را بر عهده دارد. در این معماری:
- **سازمان تفکر (ادمین‌ها):** به عنوان منبع موثق و ناشر/اهداکننده رسمی کتاب‌ها شناخته می‌شود.
- **انبار متمرکز تفکر:** موجودی کتاب‌ها، بارکدهای شناسایی و تیراژ اهدایی را در یک پایگاه داده یکپارچه مدیریت می‌کند.
- **توزیع بدون اصطکاک (Zero Friction):** تحویل کتاب‌ها به صورت قطعی و مستقیم، چه در ملاقات‌های حضوری و چه با شماره تلفن همراه، انجام می‌شود و در قفسه کاربر با برچسب اهداکننده («هدیه از طرف [نام ادمین]») جاودانه می‌ماند.

---

## ۲. مدل هویت و بارکدگذاری (Barcode & QR Architecture)

### ۲.۱. الگوی Title / Batch QR Code
برای تسهیل لجستیک چاپخانه و توزیع در همایش‌ها و دفاتر تفکر:
- به ازای هر **عنوان کتاب** در انبار تفکر، یک شناسه کوتاه منحصر‌به‌فرد (مانند `TK-RASTAN`) تولید می‌شود.
- برچسب QR یکسانی بر روی تمامی نسخه‌های چاپی این عنوان الصاق می‌گردد:  
  `https://tafakormag.ir/b/TK-RASTAN`
- با اسکن این برچسب توسط اپلیکیشن یا وب‌سایت توسط **ادمین تفکر**، سیستم مستقیماً وارد فرم اهدای این کتاب می‌شود.

---

## ۳. معماری پایگاه داده و مدل‌ها (Database Domain Models)

### ۳.۱. مدل کتاب‌های انبار تفکر (`TafakorWarehouseBook` یا `UserShelfBook(admin)`)
```python
class WarehouseBook(models.Model):
    book_title = models.ForeignKey('BookTitle', on_delete=models.PROTECT, related_name='warehouse_stock')
    total_quantity = models.PositiveIntegerField(default=1, verbose_name="کل موجودی انبار")
    donated_quantity = models.PositiveIntegerField(default=0, verbose_name="تعداد اهدا شده")
    short_code = models.CharField(max_length=20, unique=True, db_index=True) # مثلا TK-RASTAN
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_quantity(self):
        return max(0, self.total_quantity - self.donated_quantity)
```

### ۳.۲. مدل قفسه کتاب کاربر عادی (`UserGiftedBook` / `UserShelfBook`)
```python
class UserShelfBook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shelf_books')
    book_title = models.ForeignKey('BookTitle', on_delete=models.PROTECT, related_name='recipient_shelves')
    
    quantity = models.PositiveIntegerField(default=1)
    is_gift = models.BooleanField(default=True, editable=False)
    gifted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='administered_gifts')
    gifted_by_name = models.CharField(max_length=150, blank=True, default='') # نام ادمین اهداکننده
    
    gift_received_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### ۳.۳. مدل گزارش و تاریخچه اهداها (`DonationLog` / `Transfer`)
```python
class DonationLog(models.Model):
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='performed_donations')
    recipient_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_donations')
    recipient_phone = models.CharField(max_length=20, db_index=True)
    
    book_title = models.ForeignKey('BookTitle', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    
    sms_sent = models.BooleanField(default=False)
    donated_at = models.DateTimeField(default=timezone.now)
```

---

## ۴. سرویس‌ها و اندپوینت‌های API (API Specifications)

### ۴.۱. اندپوینت‌های ویژه ادمین تفکر (`Admin Only: is_staff=True`)
1. **لیست کتاب‌های انبار تفکر (تب ۱):**  
   `GET /api/v1/marketplace/warehouse/books/`
2. **ثبت عنوان جدید در انبار تفکر:**  
   `POST /api/v1/marketplace/warehouse/books/`
3. **افزایش موجودی انبار:**  
   `POST /api/v1/marketplace/warehouse/books/{id}/add-stock/`
4. **جستجوی کاربران جهت اتوکامپلیت اهدا:**  
   `GET /api/v1/accounts/users/search/?q={query}`  
   *خروجی: لیست کاربران شامل شناسه، شماره تلفن، نام و تصویر آواتار.*
5. **اهدای مستقیم کتاب به کاربر یا شماره جدید:**  
   `POST /api/v1/marketplace/warehouse/books/{id}/donate/`  
   *ورودی:*
   ```json
   {
     "quantity": 1,
     "recipient_phone": "09121234567"
   }
   ```
6. **گزارش اهدا شده‌ها (تب ۲ - Read-only Audit Log):**  
   `GET /api/v1/marketplace/warehouse/donations-report/`

### ۴.۲. اندپوینت‌های کاربر عادی (`Recipient`)
1. **کتاب‌های اهدایی به من («اهدا شده به من»):**  
   `GET /api/v1/marketplace/shelf/my-gifts/`  
   *خروجی: فقط کتاب‌هایی که با برچسب هدیه تفکر به کاربر اهدا شده است.*

---

## ۵. امنیت و قوانین یکپارچگی داده‌ها (Data Integrity & Safety)

1. **جلوگیری از تغییر یا حذف کتاب هدیه:**
   - توابع مربوط به ویرایش یا حذف کتاب در قفسه کاربر، به دلیل وجود فیلد `is_gift=True` خطای مجوز برمی‌گردانند.
2. **اتصال خودکار پس از ثبت‌نام با شماره:**
   - با ثبت‌نام هر کاربر جدید، فرآیند احراز، لاگ‌های اهدای ثبت‌شده برای آن شماره تلفن را جستجو کرده و موجودی قفسه را همگام‌سازی می‌کند.
3. **حفظ تاریخچه با Soft-Delete:**
   - در صورت لغو یا حذف یک کتاب از انبار موجودی، رکوردهای گزارش تاریخی و قفسه کاربران به هیچ وجه از بین نمی‌روند.
