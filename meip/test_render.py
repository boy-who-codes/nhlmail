import os
import sys
import django
from django.conf import settings
from django.template import loader, Context

# No redirection, just print
print("Starting script...", flush=True)

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['validator', 'web', 'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'}},
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [r'd:\00wrap\meip\templates'],
            'APP_DIRS': True,
        }],
        ROOT_URLCONF='meip.urls',  # Placeholder
        SECRET_KEY='debug_secret',
    )
    django.setup()
    print("Django setup complete.", flush=True)

from validator.models import EmailResult

print("Creating dummy result...", flush=True)
try:
    result = EmailResult(
        email='test@example.com',
        status='DELIVERABLE',
        smtp_check='Success',
        has_spf=True,
        has_dmarc=False,
        is_spammy=False,
        is_disposable=False,
        is_role_based=True,
        catch_all='No',
        domain_age_days=100
    )
    print("Dummy result created.", flush=True)

    print(f"Testing SPF Class: '{result.spf_class}'", flush=True)
    print(f"Testing DMARC Class: '{result.dmarc_class}'", flush=True)
    print(f"Testing Status Class: '{result.status_class}'", flush=True)

    print("Rendering template...", flush=True)
    t = loader.get_template('web/manual.html')
    # Use empty request for csrf checking to fail gracefully or pass dummy
    rendered = t.render({'result': result})
    print("RENDER SUCCESS!", flush=True)
    print(rendered[:500], flush=True)

except Exception as e:
    print(f"CRITICAL ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("Script finished.", flush=True)
