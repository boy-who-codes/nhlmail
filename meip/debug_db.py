import os
import django
from django.conf import settings
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meip.settings')
django.setup()

print(f"BASE_DIR: {settings.BASE_DIR}")
db_path = settings.DATABASES['default']['NAME']
print(f"DB Path from settings: {db_path}")

if not os.path.exists(db_path):
    print("CRITICAL: Database file does not exist at expected path!")
else:
    print("Database file exists.")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print("\nTables found in DB:")
    for t in sorted(tables):
        print(f" - {t}")
    
    if 'validator_emailresult' in tables:
        print("\nSUCCESS: 'validator_emailresult' table IS present.")
    else:
        print("\nFAILURE: 'validator_emailresult' table is MISSING.")
    conn.close()
