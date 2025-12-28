import os, django, sys

try:
    with open('migration_status.txt', 'w') as f:
        f.write("Starting migration...\n")
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meip.settings")
        try:
            django.setup()
            f.write("Django setup complete.\n")
        except Exception as e:
            f.write(f"Django setup failed: {e}\n")
            raise

        from django.core.management import call_command
        try:
            call_command("migrate", "validator")
            f.write("Migration 'validator' applied successfully.\n")
        except Exception as e:
             f.write(f"Migration failed: {e}\n")

        print("Done")
except Exception as outer:
    print(f"Outer error: {outer}")
