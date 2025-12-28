@echo off
cd /d d:\00wrap
call venv\Scripts\activate
echo Installing requirements...
pip install -r requirements.txt
cd meip
echo Applying migrations...
python manage.py makemigrations
python manage.py migrate
echo Starting server...
python manage.py runserver 0.0.0.0:8000
