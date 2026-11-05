#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quran Audio S3 Sync Script - Reciter: استاد عبدالباسط (Abdul Basit)
------------------------------------------------------------------
این اسکریپت صوت‌های آیه-به-آیه استاد عبدالباسط را از منابع رسمی و تمیز
(Quran.com CDN - بدون سکوت‌های اضافی انتهای آیه) دریافت کرده و مستقیماً
در باکت S3 (مانند MinIO یا S3 شرکت) بارگذاری می‌کند.

قابلیت‌ها:
  - بدون نیاز به نصب پکیج جانبی (بدون نیاز به boto3 با استفاده از استاندارد SigV4 داخلی)
  - قابلیت Resume (رد کردن فایل‌هایی که قبلاً آپلود شده‌اند)
  - بررسی خودکار سلامت فایل MP3 (جلوگیری از آپلود فایل ناقص یا صفحات فیلترینگ)
  - امکان دانلود سوره خاص یا تمام ۱۱۴ سوره
"""

import sys
import os
import argparse
import hashlib
import hmac
import datetime
import urllib.request
import urllib.error
import time

# پشتیبانی از یونیکد، فارسی و ایموجی در ترمینال ویندوز
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# تعداد آیات تمام ۱۱۴ سوره قرآن کریم به ترتیب
AYAH_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6
]

# منابع دانلود مطمئن برای صوت عبدالباسط (سورس‌های رسمی بدون سکوت انتهای آیه)
SOURCE_URLS = [
    "https://verses.quran.com/AbdulBaset/Murattal/mp3/{surah:03d}{ayah:03d}.mp3",
    "https://audio.qurancdn.com/AbdulBaset/Murattal/mp3/{surah:03d}{ayah:03d}.mp3",
    "https://www.everyayah.com/data/Abdul_Basit_Murattal_192kbps/{surah:03d}{ayah:03d}.mp3"
]

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing

def s3_head_object(endpoint, bucket, s3_key, access_key, secret_key, region='us-east-1'):
    """بررسی اینکه آیا فایل از قبل در S3 وجود دارد یا خیر"""
    endpoint = endpoint.rstrip('/')
    host = endpoint.split('://')[-1]
    
    t = datetime.datetime.now(datetime.timezone.utc)
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    canonical_uri = f'/{bucket}/{s3_key}'
    payload_hash = hashlib.sha256(b'').hexdigest()
    
    canonical_headers = (
        f'host:{host}\n'
        f'x-amz-content-sha256:{payload_hash}\n'
        f'x-amz-date:{amz_date}\n'
    )
    signed_headers = 'host;x-amz-content-sha256;x-amz-date'
    
    canonical_request = (
        f'HEAD\n'
        f'{canonical_uri}\n\n'
        f'{canonical_headers}\n'
        f'{signed_headers}\n'
        f'{payload_hash}'
    )
    
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f'{date_stamp}/{region}/s3/aws4_request'
    string_to_sign = (
        f'{algorithm}\n'
        f'{amz_date}\n'
        f'{credential_scope}\n'
        f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
    )
    
    signing_key = get_signature_key(secret_key, date_stamp, region, 's3')
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    auth_header = (
        f'{algorithm} Credential={access_key}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, Signature={signature}'
    )
    
    url = f'{endpoint}{canonical_uri}'
    headers = {
        'Host': host,
        'x-amz-date': amz_date,
        'x-amz-content-sha256': payload_hash,
        'Authorization': auth_header
    }
    
    req = urllib.request.Request(url, headers=headers, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        return False
    except Exception:
        return False

def s3_upload_file(endpoint, bucket, s3_key, file_data, access_key, secret_key, region='us-east-1', content_type='audio/mpeg'):
    """آپلود استاندارد داده با امضای AWS SigV4 به S3"""
    endpoint = endpoint.rstrip('/')
    host = endpoint.split('://')[-1]
    
    t = datetime.datetime.now(datetime.timezone.utc)
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    canonical_uri = f'/{bucket}/{s3_key}'
    payload_hash = hashlib.sha256(file_data).hexdigest()
    
    canonical_headers = (
        f'content-type:{content_type}\n'
        f'host:{host}\n'
        f'x-amz-content-sha256:{payload_hash}\n'
        f'x-amz-date:{amz_date}\n'
    )
    signed_headers = 'content-type;host;x-amz-content-sha256;x-amz-date'
    
    canonical_request = (
        f'PUT\n'
        f'{canonical_uri}\n\n'
        f'{canonical_headers}\n'
        f'{signed_headers}\n'
        f'{payload_hash}'
    )
    
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f'{date_stamp}/{region}/s3/aws4_request'
    string_to_sign = (
        f'{algorithm}\n'
        f'{amz_date}\n'
        f'{credential_scope}\n'
        f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
    )
    
    signing_key = get_signature_key(secret_key, date_stamp, region, 's3')
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    auth_header = (
        f'{algorithm} Credential={access_key}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, Signature={signature}'
    )
    
    url = f'{endpoint}{canonical_uri}'
    headers = {
        'Content-Type': content_type,
        'Host': host,
        'x-amz-date': amz_date,
        'x-amz-content-sha256': payload_hash,
        'Authorization': auth_header,
        'Content-Length': str(len(file_data))
    }
    
    req = urllib.request.Request(url, data=file_data, headers=headers, method='PUT')
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status in (200, 204)

def is_valid_mp3(data: bytes) -> bool:
    """اعتبارسنجی اولیه ساختار فایل صوتی MP3"""
    if len(data) < 5000:
        return False
    # اگر با تگ HTML یا JSON شروع شود فایل خراب یا صفحه مسدودسازی است
    if data[0] in (0x3C, 0x7B):  # '<' or '{'
        return False
    # هدر ID3v2
    if data.startswith(b'ID3'):
        return True
    # فریم سینک MPEG (0xFF و بیت‌های بعدی)
    if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return True
    return True

def download_audio(surah: int, ayah: int) -> bytes:
    """دانلود صوت یک آیه از سورس‌های موجود با مکانیسم Retry"""
    for url_pattern in SOURCE_URLS:
        url = url_pattern.format(surah=surah, ayah=ayah)
        for attempt in range(1, 3):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        data = resp.read()
                        if is_valid_mp3(data):
                            return data
            except Exception:
                time.sleep(0.3)
    return b''

def main():
    parser = argparse.ArgumentParser(description="دانلود و آپلود صوت‌های استاد عبدالباسط در S3")
    parser.add_argument("--endpoint", default=os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"), help="آدرس سرور S3")
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET_NAME", "quran-audio"), help="نام باکت")
    parser.add_argument("--access-key", default=os.getenv("S3_ACCESS_KEY", "admin"), help="Access Key")
    parser.add_argument("--secret-key", default=os.getenv("S3_SECRET_KEY", "adminpassword123"), help="Secret Key")
    parser.add_argument("--subfolder", default="Abdul_Basit_Murattal_192kbps", help="نام پوشه قاری در باکت")
    parser.add_argument("--surah", type=int, default=None, help="شماره سوره خاص برای دانلود (مثلاً 1 برای حمد)")
    parser.add_argument("--force", action="store_true", help="آپلود مجدد فایل‌ها حتی اگر از قبل وجود داشته باشند")
    
    args = parser.parse_args()
    
    print("=" * 65)
    print("🚀 شروع فرآیند همگام‌سازی صوت‌های استاد عبدالباسط با S3")
    print(f"📦 سرور S3: {args.endpoint} | باکت: {args.bucket}")
    print(f"📁 پوشه قاری در S3: {args.subfolder}")
    print("=" * 65)

    if args.surah:
        if args.surah < 1 or args.surah > 114:
            print("❌ شماره سوره نامعتبر است (باید بین ۱ تا ۱۱۴ باشد).")
            sys.exit(1)
        surah_list = [args.surah]
    else:
        surah_list = list(range(1, 115))

    total_uploaded = 0
    total_skipped = 0
    total_failed = 0

    for s in surah_list:
        ayah_count = AYAH_COUNTS[s - 1]
        print(f"\n📖 در حال پردازش سوره {s:03d} (شامل {ayah_count} آیه)...")
        
        for a in range(1, ayah_count + 1):
            fname = f"{s:03d}{a:03d}.mp3"
            s3_key = f"{args.subfolder}/{fname}"
            
            # بررسی وجود فایل در S3 برای سرعت بیشتر
            if not args.force:
                if s3_head_object(args.endpoint, args.bucket, s3_key, args.access_key, args.secret_key):
                    print(f"  ⏭️ {fname} از قبل موجود است (رد شد).")
                    total_skipped += 1
                    continue

            # دانلود صوت
            print(f"  ⬇️ در حال دانلود {fname}...", end="", flush=True)
            audio_data = download_audio(s, a)
            
            if not audio_data:
                print(" ❌ خطا در دانلود از تمام سورس‌ها!")
                total_failed += 1
                continue
                
            # آپلود در S3
            try:
                success = s3_upload_file(
                    endpoint=args.endpoint,
                    bucket=args.bucket,
                    s3_key=s3_key,
                    file_data=audio_data,
                    access_key=args.access_key,
                    secret_key=args.secret_key
                )
                if success:
                    print(f" ✅ در S3 ذخیره شد ({len(audio_data):,} بایت)")
                    total_uploaded += 1
                else:
                    print(" ❌ خطا در پاسخ سرور S3")
                    total_failed += 1
            except Exception as e:
                print(f" ❌ خطای آپلود: {e}")
                total_failed += 1

    print("\n" + "=" * 65)
    print("🎉 پایان عملیات همگام‌سازی:")
    print(f"  ✅ فایل‌های آپلود شده جدید: {total_uploaded}")
    print(f"  ⏭️ فایل‌های قبلی بدون تغییر: {total_skipped}")
    print(f"  ❌ موارد ناموفق: {total_failed}")
    print("=" * 65)

if __name__ == "__main__":
    main()
