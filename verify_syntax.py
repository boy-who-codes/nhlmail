import os
import sys
import django

sys.path.append('d:\\00wrap')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meip.settings")
django.setup()

try:
    from meip.validator import engine
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
