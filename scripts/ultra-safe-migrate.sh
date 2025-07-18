#!/bin/bash

# Ultra-Safe Migration Script for Django Multi-Tenant App
# This script handles migrations safely for both public schema and tenants

set -e  # Exit on any error

echo "🚀 Starting ultra-safe migration process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    log_error "manage.py not found. Are we in the right directory?"
    exit 1
fi

# Check Django settings
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    log_error "DJANGO_SETTINGS_MODULE environment variable not set"
    exit 1
fi

log_info "Using Django settings: $DJANGO_SETTINGS_MODULE"

# Check database connection
log_info "Testing database connection..."
python manage.py dbshell --command="SELECT 1;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "Database connection failed"
    exit 1
fi
log_info "Database connection successful"

# Create migration files if needed
log_info "Checking for new migrations..."
python manage.py makemigrations --check --dry-run
if [ $? -eq 0 ]; then
    log_info "No new migrations needed"
else
    log_warning "New migrations detected, but we're not auto-generating them in production"
fi

# Run migrations for public schema (shared apps)
log_info "Running migrations for public schema..."
python manage.py migrate_schemas --shared --verbosity=2

# Run migrations for tenant schemas
log_info "Running migrations for tenant schemas..."
python manage.py migrate_schemas --verbosity=2

# Collect static files
log_info "Collecting static files..."
python manage.py collectstatic --noinput --verbosity=1

# Run Django system checks
log_info "Running Django system checks..."
python manage.py check --verbosity=2

# Optional: Create superuser if needed (only in development)
if [ "$ENVIRONMENT" = "development" ]; then
    log_info "Development environment detected - you may need to create a superuser manually"
fi

log_info "✅ Ultra-safe migration completed successfully!"
echo "🎉 Your application is ready to deploy!"
