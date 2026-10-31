import urllib.request
import json
import sys
import time

# تنظیم انکودینگ ترمینال
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# پیکربندی سرورها
LIVE_BASE = "https://tafakormag.ir"
STAGING_BASE = "http://192.168.1.106:8085"
STAGING_TOKEN = "042ba941ce5d898da1e22c77d25514f81b19cb86"

# غیرفعال‌سازی پروکسی برای ارتباط با شبکه محلی و لایو
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def api_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with opener.open(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[-] خطا در دریافت اطلاعات از {url}: {e}")
        return None

def api_post_staging(endpoint, payload):
    url = f"{STAGING_BASE}{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Token {STAGING_TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
    )
    try:
        with opener.open(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[-] خطا در ثبت داده در استیجینگ {url}: {e}")
        return None

def get_existing_staging_topics():
    topics = api_get(f"{STAGING_BASE}/api/notes/topics/")
    if not topics:
        return {}
    return {t['name']: t['id'] for t in topics}

def sync_topics_and_posts(topics_config):
    existing_topics = get_existing_staging_topics()
    print(f"[*] تاپیک‌های فعلی در سرور استیجینگ: {existing_topics}\n")

    for live_id, config in topics_config.items():
        name = config['name']
        limit = config.get('limit', 50)
        badge = config.get('badge', '')
        desc = config.get('description', '')

        print(f"==================================================")
        print(f"[*] پردازش تاپیک: '{name}' (لایو ID: {live_id})")

        # ۱. ساخت یا پیدا کردن تاپیک در استیجینگ
        if name in existing_topics:
            staging_topic_id = existing_topics[name]
            print(f"[+] تاپیک از قبل در استیجینگ موجود است (ID: {staging_topic_id})")
        else:
            created = api_post_staging('/api/notes/topics/', {
                'name': name,
                'description': desc,
                'post_badge': badge
            })
            if not created or 'id' not in created:
                print(f"[-] ناموفق در ایجاد تاپیک {name}")
                continue
            staging_topic_id = created['id']
            existing_topics[name] = staging_topic_id
            print(f"[+] تاپیک جدید در استیجینگ ایجاد شد (ID: {staging_topic_id})")

        # ۲. واکشی پست‌ها از سرور لایو
        print(f"[*] دریافت {limit} پست آخر از سرور لایو...")
        live_posts_url = f"{LIVE_BASE}/api/notes/?topic={live_id}&page_size={limit}"
        posts_resp = api_get(live_posts_url)
        if not posts_resp or 'results' not in posts_resp:
            print(f"[-] پستی برای تاپیک {live_id} یافت نشد.")
            continue

        posts = posts_resp['results']
        total_found = posts_resp.get('count', len(posts))
        print(f"[+] تعداد {len(posts)} پست از مجموع {total_found} پست دریافت شد.")

        # معکوس کردن پست‌ها تا از قدیمی به جدید اضافه شوند و ترتیب زمانی حفظ شود
        posts_to_insert = list(reversed(posts))

        success_count = 0
        for idx, post in enumerate(posts_to_insert, 1):
            content = post.get('content') or ''
            media_type = post.get('media_type') or 'text'
            
            payload = {
                'topic': staging_topic_id,
                'content': content,
                'media_type': media_type
            }

            res = api_post_staging('/api/notes/', payload)
            if res and 'id' in res:
                success_count += 1
                if idx % 10 == 0 or idx == len(posts_to_insert):
                    print(f"    -> {idx}/{len(posts_to_insert)} پست با موفقیت ثبت شد.")
            else:
                print(f"    [-] خطا در ثبت پست {idx}")
            
            time.sleep(0.05)  # جلوگیری از بار اضافی بر روی سرور

        print(f"[OK] تاپیک '{name}' با {success_count} پست همگام‌سازی شد.\n")

if __name__ == '__main__':
    # پیکربندی تاپیک‌های مورد نظر و تعداد پست‌های هرکدام برای شبیه‌سازی سریع و کاربردی
    TOPICS_CONFIG = {
        24: {
            'name': 'مجله تفکر',
            'limit': 50,
            'badge': '@tafakormag',
            'description': 'کانال اصلی مجله تفکر حاوی آیات قرآن، اشعار و آموزه‌ها'
        },
        27: {
            'name': 'مجله تفکر از ۲۶ مرداد',
            'limit': 25,
            'badge': '@tafakormag',
            'description': 'آرشیو مجله تفکر از تاریخ ۲۶ مرداد'
        },
        30: {
            'name': 'امین ادهمی (( آرشیو))',
            'limit': 25,
            'badge': '',
            'description': 'آرشیو یادداشت‌ها و اشعار امین ادهمی'
        },
        32: {
            'name': 'آزمایشگاه کسب کار حسابرو',
            'limit': 15,
            'badge': '@hesabrolab',
            'description': 'مباحث کسب‌وکار و تجربیات حسابرو'
        },
        39: {
            'name': 'تست',
            'limit': 10,
            'badge': '',
            'description': 'تاپیک آزمایشی کاربر'
        }
    }

    print(f"=== شروع همگام‌سازی و ساخت محیط شبیه‌سازی روی لپ‌تاپ اوبونتو ===")
    sync_topics_and_posts(TOPICS_CONFIG)
    print(f"=== عملیات شبیه‌سازی با موفقیت به پایان رسید ===")

