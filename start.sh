#!/bin/bash

echo "Running Django migrations..."
python manage.py migrate --fake-initial 2>&1 || echo "Migrations skipped (already applied)"

echo "Creating superuser..."
python manage.py shell << END
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'super_admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not username or not password:
    print("⚠ Superuser credentials not fully set in environment variables")
else:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"✓ Superuser '{username}' created")
    else:
        print(f"ℹ Superuser '{username}' already exists, skipping")
END

echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

echo "Starting Django development server on port $PORT..."
gunicorn poc_fms.wsgi:application --bind 0.0.0.0:$PORT


