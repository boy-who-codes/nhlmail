@echo off
cd meip
..\venv\Scripts\python.exe manage.py check > check_log.txt 2>&1
..\venv\Scripts\python.exe manage.py makemigrations > make_log.txt 2>&1
..\venv\Scripts\python.exe manage.py migrate > migrate_log.txt 2>&1
