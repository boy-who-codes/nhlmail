import os
import sys
import django
from django.conf import settings
from django.db import connection, connections
from pathlib import Path
import shutil

# 1. Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meip.settings')
django.setup()

print("=== DIAGNOSTIC REPORT ===")
print(f"Base Dir: {settings.BASE_DIR}")
db_conf = settings.DATABASES['default']
print(f"DB Engine: {db_conf['ENGINE']}")
print(f"DB Name (configured): {db_conf['NAME']}")
real_db_path = Path(db_conf['NAME']).resolve()
print(f"DB Path (absolute): {real_db_path}")

# 2. Check Installed Apps
print(f"\nInstalled Apps: {settings.INSTALLED_APPS}")
from django.apps import apps
is_loaded = apps.is_installed('validator')
print(f"Is 'validator' app loaded? {is_loaded}")
if is_loaded:
    conf = apps.get_app_config('validator')
    print(f"Validator Path: {conf.path}")
    print(f"Validator Models: {list(conf.models.keys())}")

# 3. Check for Migrations Directory
mig_dir = Path(conf.path) / 'migrations'
print(f"\nMigrations Dir: {mig_dir}")
print(f"Exists? {mig_dir.exists()}")
if mig_dir.exists():
    print(f"Contents: {[f.name for f in mig_dir.iterdir()]}")
else:
    print("MIGRATIONS DIR MISSING! Creating it...")
    mig_dir.mkdir(parents=True, exist_ok=True)
    (mig_dir / '__init__.py').touch()

# 4. Check DB Tables
def check_tables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
    return tables

tables_before = check_tables()
print(f"\nTables BEFORE migration: {sorted(tables_before)}")

# 5. Force Make Migrations
from django.core.management import call_command
print("\n>>> Running makemigrations validator...")
try:
    call_command('makemigrations', 'validator')
    print("makemigrations success.")
except Exception as e:
    print(f"makemigrations FAILED: {e}")

# 6. Force Migrate
print(">>> Running migrate...")
try:
    call_command('migrate')
    print("migrate success.")
except Exception as e:
    print(f"migrate FAILED: {e}")

# 7. Verify Tables Again
tables_after = check_tables()
print(f"\nTables AFTER migration: {sorted(tables_after)}")

if 'validator_emailresult' in tables_after:
    print("\n[SUCCESS] Table 'validator_emailresult' is present.")
else:
    print("\n[CRITICAL FAILURE] Table 'validator_emailresult' is STILL MISSING.")

print("=== END REPORT ===")
