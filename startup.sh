#!/bin/bash

# Phone Shop - Azure Deployment Startup Script

set -e  # Exit on any error

# Configure Python
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Set Django environment to production
export DJANGO_SETTINGS_MODULE=phoneshop.settings

# Get app directory
APP_DIR=/home/site/wwwroot

# Change to app directory
cd $APP_DIR

echo "Starting Phone Shop deployment..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files (CSS, images) for production
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create necessary directories
mkdir -p logs
mkdir -p media/products

# Set proper permissions for logs and media
chmod -R 755 logs media

echo "Deployment complete. Starting Gunicorn..."

# Start the server using Gunicorn
# "phoneshop.wsgi" points to phoneshop/wsgi.py
# Use more workers and threads for better performance
gunicorn \
    --bind=0.0.0.0:8000 \
    --timeout 600 \
    --workers=3 \
    --worker-class=sync \
    --worker-tmp-dir=/dev/shm \
    --max-requests=1000 \
    --access-logfile - \
    --error-logfile - \
    phoneshop.wsgi