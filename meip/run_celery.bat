@echo off
cd /d "%~dp0"
echo Starting MEIP Celery Worker (Multi-Threaded)...
..\venv\Scripts\celery.exe -A meip worker -l info -P threads --concurrency=4
pause
pause

