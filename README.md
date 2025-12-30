# Project: NHL Mail Validation

## Overview

This repository contains a Python‑based email validation and verification system used for the **NHL Mail** project.  The core features include:
- SMTP probing with catch‑all detection
- DNS checks (MX, SPF, DMARC, DKIM)
- Firewall / security‑gateway detection (Proofpoint, Barracuda, Mimecast, Cisco ESA)
- Confidence scoring and risk classification
- Celery‑based asynchronous batch processing (Windows compatible)

## Repository Structure

```
00wrap/
├─ .env                 # Environment variables
├─ .platform/          # Platform‑specific configuration (e.g., routes.yaml)
├─ diagnose_smtp.py    # SMTP diagnostic utilities
├─ val.py               # Main validation entry point
├─ meip/                # Django project for the web UI
│   ├─ manage.py
│   ├─ web/            # Django app containing URLs, views, templates
│   └─ ...
├─ run_celery_windows.bat  # Helper script to start Celery on Windows
└─ README.md            # This file – project documentation
```

## Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)
- **Git** (optional, for cloning the repo)
- **Docker** (optional, for containerised development)
- **Windows, macOS, or Linux** – the project works on all platforms.  Windows users should run the provided batch scripts for Celery.

## Installation

```bash
# Clone the repository
git clone https://github.com/your‑org/nhlmail.git
cd nhlmail/00wrap

# Create a virtual environment (recommended)
python -m venv venv
# Activate the environment
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file and edit the values:
   ```bash
   cp .env.example .env
   ```
2. Set the following variables in `.env`:
   - `SMTP_PROBE_TIMEOUT` – timeout in seconds for SMTP probes (default: 10)
   - `CELERY_BROKER_URL` – e.g., `redis://localhost:6379/0`
   - `CELERY_RESULT_BACKEND` – e.g., `redis://localhost:6379/1`
   - `VERIFICATION_IP_POOL` – path to a JSON file containing verification IPs

## Running the Application

### Command‑line validation

```bash
python val.py --email test@example.com
```

### Web UI (Django)

```bash
# Apply migrations
python meip/manage.py migrate

# Start the development server
python meip/manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

### Celery Workers (Windows)

```bash
run_celery_windows.bat
```

The batch UI will now be able to process large email lists asynchronously.

## Testing

```bash
pytest
```

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome‑feature`).
3. Write tests for your changes.
4. Submit a pull request.

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.
