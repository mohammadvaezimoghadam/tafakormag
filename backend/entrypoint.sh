#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating cache table..."
python manage.py createcachetable

echo "Starting Gunicorn..."
gunicorn note_platform.wsgi:application --bind 0.0.0.0:8000 --workers 3