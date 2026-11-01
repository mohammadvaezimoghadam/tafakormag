#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating cache table..."
python manage.py createcachetable

echo "Importing canonical Quran Surahs, Juzs, and Seed Editions..."
python manage.py import_quran --seed || true

echo "Starting Gunicorn..."
gunicorn note_platform.wsgi:application --bind 0.0.0.0:8000 --workers 3