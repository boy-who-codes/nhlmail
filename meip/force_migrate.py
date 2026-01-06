import os
import sys
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meip.settings')
django.setup()

print("Running makemigrations...")
try:
    call_command('makemigrations', 'validator')
    print("Makemigrations success.")
except Exception as e:
    print(f"Makemigrations failed: {e}")

print("Running migrate...")
try:
    call_command('migrate')
    print("Migrate success.")
except Exception as e:
    print(f"Migrate failed: {e}")
