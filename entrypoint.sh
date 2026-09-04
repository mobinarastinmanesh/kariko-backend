#!/bin/sh
set -e

echo "⏳ Waiting for database..."
until python -c "
import os, sys
import psycopg2
try:
    psycopg2.connect(
        dbname=os.environ.get('DB_NAME','kariko'),
        user=os.environ.get('DB_USER','kariko'),
        password=os.environ.get('DB_PASSWORD','kariko'),
        host=os.environ.get('DB_HOST','db'),
        port=os.environ.get('DB_PORT','5432'),
    )
except psycopg2.OperationalError:
    sys.exit(1)
"; do
  echo "  db not ready, retrying in 2s..."
  sleep 2
done
echo "✅ Database is ready."

echo "⏳ Running migrations..."
python manage.py migrate --noinput --settings=${DJANGO_SETTINGS_MODULE:-config.settings.production}

echo "⏳ Collecting static files..."
python manage.py collectstatic --noinput --settings=${DJANGO_SETTINGS_MODULE:-config.settings.production}

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --env DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.production}
