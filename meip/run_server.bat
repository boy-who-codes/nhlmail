@echo off
cd /d "%~dp0"
echo Starting MEIP Server...
..\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
pause
