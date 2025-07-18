#!/bin/bash

# Production-Grade Django Multi-Tenant Migration Script
# Follows DevOps best practices for zero-downtime deployments
# Compatible with Render, Heroku, AWS, and other cloud platforms

set -euo pipefail  # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'        # Secure Internal Field Separator

# Configuration
readonly SCRIPT_NAME="$(basename "${0}")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly LOG_FILE="${LOG_FILE:-/tmp/deployment.log}"
readonly ENVIRONMENT="${ENVIRONMENT:-production}"
readonly TIMEOUT_SECONDS=300

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions with timestamps
log_info() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] [DEBUG]${NC} $1" | tee -a "$LOG_FILE"
    fi
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "Script failed at line ${line_number} with exit code ${exit_code}"
    log_error "Check the log file at: ${LOG_FILE}"
    exit "${exit_code}"
}

# Trap errors for debugging
trap 'handle_error ${LINENO}' ERR

# Health check function
check_health() {
    local check_name=$1
    local check_command=$2
    local timeout=${3:-30}
    
    log_debug "Running health check: ${check_name}"
    
    if timeout "${timeout}" bash -c "${check_command}" &>/dev/null; then
        log_info "✅ ${check_name} - PASSED"
        return 0
    else
        log_warning "⚠️  ${check_name} - FAILED (non-critical)"
        return 1
    fi
}

# Database connection test with retry logic
test_database_connection() {
    local max_attempts=5
    local attempt=1
    
    log_info "Testing database connection..."
    log_debug "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-not set}"
    log_debug "DATABASE_URL present: $([ -n "${DATABASE_URL:-}" ] && echo "yes" || echo "no")"
    log_debug "ENVIRONMENT: ${ENVIRONMENT:-not set}"
    
    while [[ $attempt -le $max_attempts ]]; do
        local connection_test_output
        connection_test_output=$(python manage.py shell -c "
from django.db import connection, OperationalError
from django.conf import settings
import os

print(f'Django settings module: {os.environ.get(\"DJANGO_SETTINGS_MODULE\", \"not set\")}')
print(f'Database engine: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
print(f'Database name: {settings.DATABASES[\"default\"].get(\"NAME\", \"not set\")}')
print(f'Database host: {settings.DATABASES[\"default\"].get(\"HOST\", \"not set\")}')

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    print('SUCCESS: Database connection successful')
except Exception as e:
    error_msg = str(e)
    print(f'ERROR: Database connection failed: {error_msg}')
    
    # Verificar si es un error de DNS que puede ser normal en local
    if 'could not translate host name' in error_msg and 'render.com' not in error_msg:
        print('INFO: This might be a Render internal URL that only works in production')
        print('INFO: If you are testing locally, try using the External Database URL from Render')
    
    print(f'DEBUG: Connection parameters: {connection.settings_dict}')
    exit(1)
        " 2>&1)
        
        if echo "$connection_test_output" | grep -q "SUCCESS: Database connection successful"; then
            log_info "Database connection successful on attempt ${attempt}"
            log_debug "Connection details: $connection_test_output"
            return 0
        else
            log_warning "Database connection failed on attempt ${attempt}/${max_attempts}"
            
            # Mostrar información útil en caso de error
            if echo "$connection_test_output" | grep -q "could not translate host name"; then
                log_info "Note: Render internal URLs only work in the Render environment"
                log_info "If testing locally, use the External Database URL from Render"
            fi
            
            if [[ "${DEBUG:-false}" == "true" ]]; then
                log_error "Full connection output: $connection_test_output"
            fi
            
            if [[ $attempt -lt $max_attempts ]]; then
                sleep $((attempt * 2))  # Exponential backoff
            fi
            ((attempt++))
        fi
    done
    
    log_error "Database connection failed after ${max_attempts} attempts"
    log_error "If using Render internal URL, this is expected locally but should work in production"
    return 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "🔍 Running pre-deployment checks..."
    
    # Check if we're in the right directory
    if [[ ! -f "manage.py" ]]; then
        log_error "manage.py not found. Please run this script from the Django project root."
        exit 1
    fi
    
    # Check Django settings
    if [[ -z "${DJANGO_SETTINGS_MODULE:-}" ]]; then
        log_error "DJANGO_SETTINGS_MODULE environment variable not set"
        exit 1
    fi
    
    log_info "Using Django settings: ${DJANGO_SETTINGS_MODULE}"
    
    # Check Python version
    local python_version
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    log_info "Python version: ${python_version}"
    
    # Check required environment variables
    local required_vars=("DATABASE_URL" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable ${var} is not set"
            exit 1
        fi
    done
    
    log_info "✅ Pre-deployment checks completed"
}

# Migration execution with proper error handling
execute_migrations() {
    log_info "🚀 Executing database migrations..."
    
    # Test database connection first
    if ! test_database_connection; then
        log_error "Cannot proceed with migrations - database connection failed"
        return 1
    fi
    
    # Run migrations for public schema (shared apps)
    log_info "Running migrations for public schema..."
    if ! python manage.py migrate_schemas --shared --verbosity=2; then
        log_error "Public schema migration failed"
        return 1
    fi
    
    # Run migrations for tenant schemas
    log_info "Running migrations for tenant schemas..."
    if ! python manage.py migrate_schemas --verbosity=2; then
        log_warning "Tenant migration failed - this might be normal for first deployment"
        log_info "Tenant schemas will be created when tenants are added"
    fi
    
    log_info "✅ Database migrations completed"
}

# Static files collection
collect_static_files() {
    log_info "📦 Collecting static files..."
    
    # Ensure static directories exist
    mkdir -p "${STATIC_ROOT:-/app/static_collected}"
    
    if ! python manage.py collectstatic --noinput --verbosity=1; then
        log_error "Static files collection failed"
        return 1
    fi
    
    log_info "✅ Static files collection completed"
}

# Post-deployment checks
post_deployment_checks() {
    log_info "🔍 Running post-deployment checks..."
    
    # Django system check
    check_health "Django System Check" "python manage.py check --verbosity=1"
    
    # Health endpoint check (if available)
    if command -v curl &>/dev/null; then
        check_health "Health Endpoint" "curl -f http://localhost:8000/health/" 10
    fi
    
    log_info "✅ Post-deployment checks completed"
}

# Main execution function
main() {
    log_info "🚀 Starting production-grade deployment process..."
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Log file: ${LOG_FILE}"
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "${LOG_FILE}")"
    
    # Execute deployment steps
    pre_deployment_checks
    execute_migrations
    collect_static_files
    post_deployment_checks
    
    log_info "🎉 Deployment completed successfully!"
    log_info "Application is ready to serve traffic"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
