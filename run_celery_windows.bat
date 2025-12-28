@echo off
echo Starting Celery Worker (Pool=Solo for Windows)...
cd meip
celery -A meip worker -l info -P solo
pause
