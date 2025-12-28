@echo off
cd d:\00wrap
call venv\Scripts\activate
cd meip
echo Making migrations for validator...
python manage.py makemigrations validator
echo Migrating...
python manage.py migrate
