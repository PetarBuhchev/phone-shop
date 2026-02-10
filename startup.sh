#!/bin/bash

# Apply database migrations
python manage.py migrate

# Collect static files (CSS, images) so they work in production
python manage.py collectstatic --noinput

# Start the server using Gunicorn
# "phoneshop.wsgi" points to phoneshop/wsgi.py
gunicorn --bind=0.0.0.0 --timeout 600 phoneshop.wsgi