@echo off
cd d:\00wrap
call venv\Scripts\activate
cd meip

echo Stopping any running python processes...
taskkill /F /IM python.exe /T

echo checking migrations...
if not exist "validator\migrations\__init__.py" (
    echo Creating migrations dir...
    mkdir validator\migrations
    type nul > validator\migrations\__init__.py
)

echo deleting old db...
if exist "db.sqlite3" del db.sqlite3

echo Making migrations for validator...
python manage.py makemigrations validator
python manage.py makemigrations

echo Migrating...
python manage.py migrate

echo Creating superuser (admin/admin)...
echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin') | python manage.py shell

echo Starting server...
python manage.py runserver 0.0.0.0:8000
