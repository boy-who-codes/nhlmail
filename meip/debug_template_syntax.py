import os
import sys
import django
from django.conf import settings
from django.template import Template, Context, TemplateSyntaxError

# Redirect stderr to a file to capture panic/errors
sys.stderr = open('syntax_error_log.txt', 'w')
sys.stdout = open('syntax_output_log.txt', 'w')

print("Starting checks...")

# Minimal Django settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }]
    )
    django.setup()

file_path = r'd:\00wrap\meip\templates\web\manual.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Checking syntax of: {file_path}")
    # Compile the template
    t = Template(content)
    print("SUCCESS: Template syntax is valid.")

except TemplateSyntaxError as e:
    print(f"FAIL: TemplateSyntaxError: {e}")
    if hasattr(e, 'django_template_source'):
         # Try to show the line
         print(f"Source info: {e.django_template_source}")

except Exception as e:
    print(f"FAIL: General Error: {type(e).__name__}: {e}")

print("Done.")
sys.stderr.close()
sys.stdout.close()
