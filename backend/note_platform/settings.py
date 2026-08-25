"""
Django settings for note_platform project.
"""

import os
import sys
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Add project root and backend folder to PYTHONPATH dynamically
sys.path.insert(0, str(BASE_DIR.parent))
sys.path.insert(0, str(BASE_DIR))

# ==============================================================================
# امنیت
# ==============================================================================
SECRET_KEY = os.getenv('SECRET_KEY', config('SECRET_KEY', default='django-insecure-change-me'))

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# ==============================================================================
# اپلیکیشن‌ها
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'apps.accounts',
    'apps.notes',
    'apps.donations',
    'apps.plugin_system',
]

# ==============================================================================
# پیکربندی سیستم پلاگین تفاخر (Tafakor Plugin System)
# ==============================================================================
INSTALLED_TAFAKOR_PLUGINS = [
    'plugins.quran',
]

# الحاق پویا و ایمن اپلیکیشن‌های پلاگین به INSTALLED_APPS
for _plugin_app in INSTALLED_TAFAKOR_PLUGINS:
    if _plugin_app not in INSTALLED_APPS:
        INSTALLED_APPS.append(_plugin_app)

# ==============================================================================
# REST Framework
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ==============================================================================
# توکن‌های ربات‌ها و کلیدهای API
# ==============================================================================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', config('TELEGRAM_BOT_TOKEN', default=''))
TELEGRAM_API_URL = os.getenv('TELEGRAM_API_URL', config('TELEGRAM_API_URL', default='https://api.telegram.org/bot'))
BALE_BOT_TOKEN = os.getenv('BALE_BOT_TOKEN', config('BALE_BOT_TOKEN', default=''))
BOT_API_KEY = os.getenv('BOT_API_KEY', config('BOT_API_KEY', default=''))
KAVENEGAR_API_KEY = os.getenv('KAVENEGAR_API_KEY', config('KAVENEGAR_API_KEY', default=''))
KAVENEGAR_SENDER = os.getenv('KAVENEGAR_SENDER', config('KAVENEGAR_SENDER', default=''))

# ==============================================================================
# پیکربندی درگاه پرداخت زرین‌پال (ZarinPal Gateway)
# ==============================================================================
ZARINPAL_SANDBOX = os.getenv('ZARINPAL_SANDBOX', config('ZARINPAL_SANDBOX', default='True')) == 'True'
ZARINPAL_MERCHANT_ID = os.getenv('ZARINPAL_MERCHANT_ID', config('ZARINPAL_MERCHANT_ID', default='00000000-0000-0000-0000-000000000000'))
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', config('FRONTEND_BASE_URL', default='http://localhost:5173'))
BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', config('BACKEND_BASE_URL', default='http://localhost:8000'))

# ==============================================================================
# مدل کاربری سفارشی
# ==============================================================================
AUTH_USER_MODEL = 'accounts.User'

# ==============================================================================
# Middleware
# ==============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================================================================
# CORS & Reverse Proxy
# ==============================================================================
CORS_ALLOW_ALL_ORIGINS = True
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==============================================================================
# مسیرهای اصلی
# ==============================================================================
ROOT_URLCONF = 'note_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'note_platform.wsgi.application'

# ==============================================================================
# دیتابیس (PostgreSQL با قابلیت بازگشت به SQLite برای تست محلی)
# ==============================================================================
if os.getenv('DB_HOST'):  # اگر متغیر محیطی وجود داشت (= محیط Docker)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'tafakor'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'admin'),
            'HOST': os.getenv('DB_HOST', 'db'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 30,
            },
        }
    }

# ==============================================================================
# اعتبارسنجی رمز
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# بین‌المللی‌سازی
# ==============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# فایل‌های استاتیک و رسانه
# ==============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==============================================================================
# Cache (Database-backed برای پشتیبانی از چند worker گانیکورن)
# ==============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

# ==============================================================================
# سایر
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# آپلود فایل (افزایش سقف حجم فایل برای تصاویر پروفایل و تاپیک‌ها)
# ==============================================================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 2147483648  # 2 GB
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400  # 25 MB

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


