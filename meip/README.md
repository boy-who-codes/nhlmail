# NIMV - NHL Internal Mail Validator

NIMV is an enterprise-grade, privacy-first email validation system designed for high accuracy and detailed intelligence. It moves beyond simple "Valid/Invalid" checks to provide deep insights into email infrastructure, security configurations, and deliverability risks.

## 🚀 Key Features

*   **Deep Validation Engine**:
    *   **Syntax & Format**: RFC-compliant syntax checking and unicode normalization.
    *   **Domain Intelligence**: Validates MX records, A records, and Domain Age.
    *   **Infrastructure Checks**: Detects Provider (Google, Outlook, Zoho, etc.), Security (SPF/DMARC), and Catch-All configurations.
    *   **Risk Analysis**: Flags Disposable domains, Role-based accounts (admin@, support@), and Greylisted servers.
    *   **SMTP Handshake**: Performs safe, quiet SMTP verifications without sending actual emails.
*   **Bulk Processing**:
    *   Asynchronous execution using **Celery & Redis**.
    *   Handles large CSV uploads without blocking the UI.
    *   Real-time progress tracking and estimated completion times.
    *   Pause/Resume/Delete batch controls.
*   **Monitoring Dashboard**:
    *   Dark-mode UI for "NOC-style" monitoring.
    *   Visual separation of Deliverable, Risky, and Undeliverable leads.
    *   Detailed verification logs (SMTP check messages, error codes).
*   **Data Export**:
    *   Export clean, filtered CSVs for marketing campaigns.

## 📂 Directory Structure

```text
meip/
├── meip/                   # Project Settings & Configuration
│   ├── settings.py         # Django Settings (Apps, DB, Redis, Email)
│   ├── urls.py             # Main Route Mapping
│   └── celery.py           # Celery App Configuration
│
├── validator/              # Core Validation Engine App
│   ├── engine.py           # The "Brain" - SMTP, DNS, & Scoring Logic
│   ├── models.py           # DB Models (ValidationBatch, EmailResult)
│   ├── tasks.py            # Celery Async Tasks definition
│   └── migrations/         # Database Schema Migrations
│
├── web/                    # Dashboard & UI App
│   ├── views.py            # Frontend Logic (Dashboard, Upload, Reports)
│   └── urls.py             # Web Routes
│
├── templates/              # HTML Templates (Tailwind CSS based)
│   ├── base.html           # Main Layout
│   └── web/                # Dashboard Pages (batch_detail.html, etc.)
│
├── media/uploads/          # Storage for uploaded CSVs
├── db.sqlite3              # Local Database
├── manage.py               # Django CLI Entry Point
├── run_celery.bat          # Windows Helper Script for Workers
└── README.md               # This Documentation
```

---

## 🛠️ Prerequisites

*   **Python 3.10+**
*   **Redis Server** (Message Broker for Async Tasks)

---

## 💻 Running Locally

### 1. Windows Setup

**A. Install Redis**
Windows does not support Redis natively. You have two options:
1.  **WSL2 (Recommended)**: Install Ubuntu on WSL and run `sudo apt install redis && sudo service redis-server start`.
2.  **Memurai**: Download and install [Memurai](https://www.memurai.com/) (Redis-compatible for Windows).
3.  **Docker**: `docker run -p 6379:6379 redis`

**B. Setup Environment**
```powershell
# Create venv
python -m venv venv
.\venv\Scripts\activate

# Install Dependencies
pip install django celery redis dnspython tldextract email-validator python-whois

# Database Setup
python manage.py migrate
```

**C. Start the System**
You need **two** separate terminal windows running simultaneously.

*Terminal 1: Web Server*
```powershell
python manage.py runserver
# Access at http://127.0.0.1:8000
```

*Terminal 2: Background Worker*
```powershell
# Use the helper script
.\run_celery.bat

# OR run manually:
celery -A meip worker --pool=solo -l info
# Note: --pool=solo is CRITICAL for Windows to avoid freeze issues
```

### 2. Linux / macOS Setup

**A. Install Redis**
*   **Ubuntu/Debian**: `sudo apt install redis-server`
*   **macOS (Homebrew)**: `brew install redis`
*   **Start Service**: `sudo service redis-server start` (Linux) or `brew services start redis` (Mac).

**B. Setup Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install django celery redis dnspython tldextract email-validator python-whois
python manage.py migrate
```

**C. Start the System**
*Terminal 1: Web Server*
```bash
python manage.py runserver
```

*Terminal 2: Background Worker*
```bash
celery -A meip worker -l info
```

---

## ☁️ Running on Google Colab (For Testing)

You can run NIMV in a Colab notebook for quick testing of the logic or even the full UI.

### Option A: Logic Testing (Headless)
Use this to test the validation engine without the UI.

```python
# 1. Install Dependencies
!pip install django dnspython tldextract email-validator python-whois

# 2. Clone Repo (or upload files)
# If uploading "meip" folder to Colab root:
import sys
import os
import django

# Add project to path
sys.path.append('/content/meip')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meip.settings")
django.setup()

# 3. Validation Test
from validator.engine import validate_email_single

email = "test@example.com"
result = validate_email_single(email)

import json
print(json.dumps(result, indent=4, str=str))
```

### Option B: Full System (with UI)
Use `pyngrok` to tunnel the Django server to the internet.

```python
# 1. Install System Deps
!apt-get install -y redis-server
!service redis-server start

# 2. Install Python Deps
!pip install django celery redis dnspython tldextract email-validator python-whois pyngrok

# 3. Prepare Project
# (Upload your 'meip' folder to /content/meip)
%cd /content/meip
!python manage.py migrate

# 4. Start Celery (Background)
import subprocess
subprocess.Popen(['celery', '-A', 'meip', 'worker', '-l', 'info'])

# 5. Start Django with Ngrok
from pyngrok import ngrok
from django.core.management import call_command
import threading

# Set your Ngrok token first!
ngrok.set_auth_token("YOUR_NGROK_AUTH_TOKEN")

# Tunnel
public_url = ngrok.connect(8000).public_url
print(f"🚀 Application running at: {public_url}")

# Run Server
!python manage.py runserver 8000
```
