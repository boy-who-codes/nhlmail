import os, django, redis
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meip.settings")
django.setup()

from validator.models import ValidationBatch

print("Checking Redis...")
try:
    r = redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=3)
    r.ping()
    print("Redis: OK")
except Exception as e:
    print(f"Redis: FAILED ({e})")

print("Checking DB...")
try:
    c = ValidationBatch.objects.filter(status__in=['PROCESSING', 'PENDING']).count()
    print(f"Active Batches: {c}")
except Exception as e:
    print(f"DB: FAILED ({e})")
