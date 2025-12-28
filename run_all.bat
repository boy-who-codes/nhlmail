@echo off
cd /d "%~dp0"
echo ==========================================
echo Starting MEIP System (Server + Worker)
echo ==========================================

echo [1/2] Starting Celery Worker...
start "MEIP Celery" cmd /k "call venv\Scripts\activate && cd meip && celery -A meip worker -l info -P solo"

echo [2/2] Starting Django Server...
timeout /t 2 >nul
start "MEIP Server" cmd /k "call venv\Scripts\activate && cd meip && python manage.py runserver 0.0.0.0:8000"

echo System Started. check the popup windows.
pause
