#!/bin/bash

# Phone Shop - Azure App Service Deployment Script
# This script should be run by Azure App Service on startup

set -e  # Exit on any error

echo "==================================="
echo "Phone Shop Azure Deployment Started"
echo "==================================="
echo "Time: $(date)"
echo "Current directory: $(pwd)"

# ===== ENVIRONMENT SETUP =====
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export DJANGO_SETTINGS_MODULE=phoneshop.settings

# Get app directory (Azure App Service root)
APP_DIR=/home/site/wwwroot
cd $APP_DIR || { echo "ERROR: Could not change to app directory"; exit 1; }

echo "[1/6] Environment configured (Python buffering disabled, Django settings loaded)"

# ===== VIRTUAL ENVIRONMENT =====
echo "[2/6] Checking Python virtual environment..."

if [ ! -d "venv" ]; then
    echo "  → Creating new virtual environment..."
    python -m venv venv || { echo "ERROR: Failed to create virtual environment"; exit 1; }
else
    echo "  → Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate || { echo "ERROR: Failed to activate virtual environment"; exit 1; }
echo "  ✓ Virtual environment activated"

# ===== DEPENDENCIES =====
echo "[3/6] Installing dependencies..."
pip install --upgrade pip setuptools wheel || { echo "ERROR: Failed to upgrade pip"; exit 1; }
pip install -r requirements.txt || { echo "ERROR: Failed to install requirements"; exit 1; }
echo "  ✓ All dependencies installed"

# ===== DATABASE MIGRATIONS =====
echo "[4/6] Applying database migrations..."
python manage.py migrate --noinput || { echo "ERROR: Migration failed"; exit 1; }
echo "  ✓ Database migrations completed"

# ===== STATIC FILES =====
echo "[5/6] Collecting static files for production..."
python manage.py collectstatic --noinput --clear --verbosity 0 || { echo "ERROR: Static file collection failed"; exit 1; }
echo "  ✓ Static files collected successfully"

# ===== DIRECTORIES =====
echo "[6/6] Setting up application directories..."
mkdir -p logs media/products logs/emails

# Set proper permissions for Azure App Service
chmod -R 755 logs media

# Create .gitkeep files to ensure directories persist
touch logs/.gitkeep media/.gitkeep logs/emails/.gitkeep

echo "  ✓ Application directories ready"

# ===== FINAL STATUS =====
echo ""
echo "==================================="
echo "✓ Deployment completed successfully!"
echo "==================================="
echo "Application is ready to serve requests"
echo "Time: $(date)"
echo ""

# Display Python and Django versions for debugging
python --version
echo "Django version:"
python -c "import django; print(django.get_version())"

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