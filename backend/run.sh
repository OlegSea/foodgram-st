#!/bin/bash

set -e

python manage.py migrate --noinput

python manage.py collectstatic --noinput

if [ "$LOAD_TEST_DATA" = "True" ]; then
    cp -r data/recipes media/
fi

python manage.py load_ingredients /data/ingredients.json

if [ "$LOAD_TEST_DATA" = "True" ]; then
    python manage.py loaddata data/test_data.json
fi

if [ "$DEBUG" = "True" ]; then
    echo "Running in DEBUG mode with Django development server"
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Running in production mode with gunicorn"
    exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi
