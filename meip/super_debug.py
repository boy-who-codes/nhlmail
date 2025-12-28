import os
import sys
import django
from django.conf import settings
from django.db import connection

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meip.settings')
django.setup()

print("=== SUPER DEBUG LOG ===")
print(f"Base Dir: {settings.BASE_DIR}")
db_path = settings.DATABASES['default']['NAME']
print(f"DB Path: {db_path}")

try:
    from validator.models import EmailResult
    print(f"Model Loaded: {EmailResult}")
    print(f"Expected Table Name: {EmailResult._meta.db_table}")
except Exception as e:
    print(f"Error loading model: {e}")

print("\n--- Database Tables ---")
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    for t in sorted(tables):
        print(f" - {t}")

print("\n--- Query Test ---")
try:
    c = EmailResult.objects.count()
    print(f"Count Query Success: {c}")
except Exception as e:
    print(f"Count Query FAILED: {e}")

print("=== END LOG ===")
