from pathlib import Path
import os
import environ
import socket
import redis

def is_redis_available(broker_url):
    try:
        # Use valid redis client to check
        r = redis.from_url(broker_url, socket_timeout=3)
        r.ping()
        return True
    except Exception as e:
        print(f"[!] Redis Check Error: {e}")
        return False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

print(f"DEBUG: BASE_DIR is {BASE_DIR}")
env_file = BASE_DIR / '.env'
print(f"DEBUG: Loading .env from {env_file}")

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'django-insecure-manual-creation-key-for-dev'),
    ALLOWED_HOSTS=(list, ['*']),
)

# Take environment variables from .env file
environ.Env.read_env(env_file)

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'validator',
    'web',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meip.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'meip.wsgi.application'

# Database
# Use SQLite for dev as per plan
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20, # Wait 20 seconds for lock release
        }
    }
}
print(f"DEBUG: Active Database Path: {DATABASES['default']['NAME']}")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
# FORCE READ from ENV or Fail (No default localhost)
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')

print(f"DEBUG: LOADED BROKER URL: {CELERY_BROKER_URL}")

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Redis Fallback Logic:
# Check the configured BROKER URL, not just localhost
if is_redis_available(CELERY_BROKER_URL):
    safe_url = CELERY_BROKER_URL.split('@')[-1] if '@' in CELERY_BROKER_URL else CELERY_BROKER_URL
    print(f"[-] Redis detected at {safe_url}. Using Async Celery.")
    CELERY_TASK_ALWAYS_EAGER = False
    CELERY_TASK_EAGER_PROPAGATES = False
else:
    print(f"[!] Redis NOT detected at configured URL. Using Eager Mode (Synchronous).")
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# MEIP Specific Config
SMTP_LIST = ["dev@meta-insyt.com"] # Default list
DISPOSABLE_DOMAINS_FILE = BASE_DIR / 'validator' / 'disposable_domains.txt'
