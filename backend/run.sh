#!/bin/bash

set -e

python manage.py migrate --noinput

python manage.py collectstatic --noinput

python manage.py load_ingredients

python manage.py shell -c "
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

try:
    if not User.objects.filter(username='admin').exists() and not User.objects.filter(email='admin@example.com').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print('Superuser created: admin/admin')
    else:
        print('Superuser already exists')
except IntegrityError as e:
    print(f'Superuser creation skipped: {e}')
except Exception as e:
    print(f'Error creating superuser: {e}')
"

if [ "$DEBUG" = "True" ]; then
    echo "Running in DEBUG mode with Django development server"
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Running in production mode with gunicorn"
    exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi
