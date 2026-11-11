#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput -v0
python manage.py seed_units
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile -
