import os
import django
from django.conf import settings
import redis

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meip.settings')
django.setup()

from meip.celery import app

def check_redis():
    print("[-] Checking Redis Connection...")
    broker_url = settings.CELERY_BROKER_URL
    print(f"    Broker URL: {broker_url}")
    try:
        r = redis.from_url(broker_url, socket_timeout=5)
        r.ping()
        print("    [SUCCESS] Redis is reachable!")
        return True
    except Exception as e:
        print(f"    [FAILURE] Redis Connection Failed: {e}")
        return False

def check_celery_config():
    print("\n[-] Checking Celery Config...")
    print(f"    ALWAYS_EAGER: {getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)}")
    print(f"    BROKER_URL from App: {app.conf.broker_url}")

def send_test_task():
    print("\n[-] Sending Test Task...")
    try:
        # We'll use the debug_task defined in celery.py
        from meip.celery import debug_task
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            print("    [INFO] Eager mode is ON. Task will run synchronously.")
        
        result = debug_task.delay()
        print(f"    [SUCCESS] Task Dispatched. ID: {result.id}")
        return result
    except Exception as e:
        print(f"    [FAILURE] Task Dispatch Failed: {e}")

if __name__ == "__main__":
    is_redis_ok = check_redis()
    check_celery_config()
    if is_redis_ok or getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        send_test_task()
    else:
        print("\n[!] Skipping Task Dispatch due to Redis failure and Eager Mode being OFF.")
