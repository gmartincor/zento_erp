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

# Create initial tenant to resolve django-tenants configuration issues
create_initial_tenant() {
    log_info "🏗️  Creating initial tenant to resolve django-tenants configuration..."
    
    # Configuration for initial tenant
    local tenant_schema="${TENANT_SCHEMA:-principal}"
    local tenant_domain="${TENANT_DOMAIN:-app.zentoerp.com}"
    local tenant_name="${TENANT_NAME:-Principal}"
    
    log_info "Tenant configuration:"
    log_info "  - Schema: ${tenant_schema}"
    log_info "  - Domain: ${tenant_domain}"
    log_info "  - Name: ${tenant_name}"
    
    local creation_output
    creation_output=$(python manage.py shell -c "
from django.db import transaction
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
import sys

try:
    Tenant = get_tenant_model()
    Domain = get_tenant_domain_model()
    
    # Check if tenant already exists
    if Tenant.objects.filter(schema_name='${tenant_schema}').exists():
        print('INFO: Tenant already exists with this schema name')
        sys.exit(0)
    
    with transaction.atomic():
        # Create tenant
        tenant = Tenant.objects.create(
            schema_name='${tenant_schema}',
            name='${tenant_name}',
            description='Initial tenant created automatically during deployment to resolve django-tenants configuration'
        )
        
        # Create domain
        domain = Domain.objects.create(
            domain='${tenant_domain}',
            tenant=tenant,
            is_primary=True
        )
        
        print(f'SUCCESS: Tenant created successfully')
        print(f'  - Name: {tenant.name}')
        print(f'  - Schema: {tenant.schema_name}')
        print(f'  - Domain: {domain.domain}')
        
except Exception as e:
    print(f'ERROR: Failed to create tenant: {e}')
    sys.exit(1)
    " 2>&1)
    
    echo "$creation_output"
    
    if echo "$creation_output" | grep -q "SUCCESS: Tenant created successfully"; then
        log_info "✅ Initial tenant created successfully"
        
        # Now run tenant migrations to create the missing tables
        log_info "🔄 Running tenant migrations to create missing tables..."
        if python manage.py migrate_schemas --verbosity=1; then
            log_info "✅ Tenant migrations completed successfully"
            return 0
        else
            log_error "❌ Tenant migrations failed after creating tenant"
            return 1
        fi
    elif echo "$creation_output" | grep -q "INFO: Tenant already exists"; then
        log_info "ℹ️  Tenant already exists, running migrations..."
        if python manage.py migrate_schemas --verbosity=1; then
            log_info "✅ Tenant migrations completed successfully"
            return 0
        else
            log_error "❌ Tenant migrations failed"
            return 1
        fi
    else
        log_error "❌ Failed to create initial tenant"
        log_error "Creation output: $creation_output"
        return 1
    fi
}

# Database state diagnosis
diagnose_database_state() {
    log_info "🔍 Diagnosing database state..."
    
    local diagnosis_output
    diagnosis_output=$(python manage.py shell -c "
from django.db import connection
from django.core.management.color import no_style
from django.db.migrations.recorder import MigrationRecorder
import sys

try:
    # Check if database is empty or has tables
    with connection.cursor() as cursor:
        # Get list of tables
        table_names = connection.introspection.table_names(cursor)
        print(f'Total tables in database: {len(table_names)}')
        
        if len(table_names) == 0:
            print('STATUS: EMPTY_DATABASE - Fresh database, ready for initial deployment')
            sys.exit(0)
        
        # Check if django_migrations table exists
        if 'django_migrations' not in table_names:
            print('STATUS: NO_MIGRATION_TABLE - Database has tables but no migration tracking')
            print(f'Existing tables: {table_names[:10]}...' if len(table_names) > 10 else f'Existing tables: {table_names}')
            sys.exit(0)
        
        # Check migration status
        recorder = MigrationRecorder(connection)
        applied_migrations = recorder.applied_migrations()
        print(f'Applied migrations count: {len(applied_migrations)}')
        
        # Check for our specific app migrations
        app_migrations = {}
        for app, migration in applied_migrations:
            if app not in app_migrations:
                app_migrations[app] = []
            app_migrations[app].append(migration)
        
        print('Applied migrations by app:')
        for app, migrations in app_migrations.items():
            print(f'  {app}: {len(migrations)} migrations')
        
        # Check if we have the key tables for our apps
        expected_tables = ['tenants_tenant', 'tenants_domain', 'business_lines', 
                          'clients', 'client_services', 'users']
        missing_tables = [table for table in expected_tables if table not in table_names]
        
        # Special check for django-tenants configuration issues
        tenant_app_tables = ['business_lines', 'clients', 'client_services', 'expenses']
        missing_tenant_tables = [table for table in tenant_app_tables if table not in table_names]
        
        if missing_tenant_tables:
            # Check if this might be a tenant app configuration issue
            cursor.execute(\"SELECT COUNT(*) FROM tenants_tenant\")
            tenant_count = cursor.fetchone()[0]
            
            if tenant_count == 0 and missing_tenant_tables:
                print(f'STATUS: TENANT_CONFIG_ISSUE - Missing tenant app tables: {missing_tenant_tables}')
                print(f'No tenants found but tenant app migrations are applied')
                print(f'This suggests tenant apps were incorrectly applied to public schema')
            else:
                print(f'STATUS: INCOMPLETE_SCHEMA - Missing tables: {missing_tables}')
        else:
            print('STATUS: COMPLETE_SCHEMA - All expected tables present')
            
except Exception as e:
    print(f'ERROR: Could not diagnose database: {e}')
    sys.exit(1)
    " 2>&1)
    
    echo "$diagnosis_output"
    
    # Parse the status and provide recommendations
    if echo "$diagnosis_output" | grep -q "STATUS: EMPTY_DATABASE"; then
        log_info "✅ Database is empty - perfect for fresh deployment"
        return 0
    elif echo "$diagnosis_output" | grep -q "STATUS: NO_MIGRATION_TABLE"; then
        log_warning "⚠️  Database has tables but no migration tracking"
        log_info "Recommendation: This might be a legacy database that needs migration setup"
        return 1
    elif echo "$diagnosis_output" | grep -q "STATUS: TENANT_CONFIG_ISSUE"; then
        log_error "🚨 CRITICAL: Tenant app configuration issue detected"
        log_error "Apps configured as TENANT_APPS but no tenants exist"
        log_info "🔧 Auto-repairing: Creating initial tenant to resolve the issue..."
        
        if create_initial_tenant; then
            log_info "✅ Tenant configuration issue resolved"
            return 0
        else
            log_error "❌ Failed to auto-repair tenant configuration"
            log_info "Recommendation: Run repair-production-db.sh script manually"
            return 1
        fi
    elif echo "$diagnosis_output" | grep -q "STATUS: INCOMPLETE_SCHEMA"; then
        log_warning "⚠️  Database schema is incomplete"
        log_info "Recommendation: Some migrations may have failed or database is corrupted"
        return 1
    elif echo "$diagnosis_output" | grep -q "STATUS: COMPLETE_SCHEMA"; then
        log_info "✅ Database schema appears complete"
        return 0
    else
        log_error "❌ Could not determine database status"
        return 1
    fi
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
    
    # Diagnose database state
    if ! diagnose_database_state; then
        log_warning "Database state diagnosis indicates potential issues"
        if [[ "${FORCE_MIGRATION:-false}" != "true" ]]; then
            log_error "Set FORCE_MIGRATION=true to proceed anyway"
            return 1
        else
            log_warning "FORCE_MIGRATION=true - proceeding despite warnings"
        fi
    fi
    
    # Run migrations for public schema (shared apps)
    log_info "Running migrations for public schema..."
    python manage.py migrate_schemas --shared --verbosity=2 --skip-checks
    
    # Run migrations for tenant schemas
    log_info "Running migrations for tenant schemas..."
    python manage.py migrate_schemas --verbosity=2 --skip-checks || {
        log_warning "Tenant migration failed - this might be normal for first deployment"
        log_info "Tenant schemas will be created when tenants are added"
    }
    
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
    
    # Django system check (critical)
    if ! check_health "Django System Check" "python manage.py check --verbosity=1"; then
        log_error "Django system check failed - this is critical"
        return 1
    fi
    
    # Health endpoint check (non-critical)
    if command -v curl &>/dev/null; then
        if check_health "Health Endpoint" "curl -f http://localhost:8000/health/" 10; then
            log_info "Health endpoint is responding correctly"
        else
            log_warning "Health endpoint check failed, but this is non-critical during deployment"
            log_info "The application may not be fully started yet during pre-deploy phase"
        fi
    fi
    
    log_info "✅ Post-deployment checks completed"
}

# Display usage information
show_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Production-Grade Django Multi-Tenant Migration Script

OPTIONS:
    -h, --help              Show this help message
    -d, --diagnose          Only diagnose database state, don't migrate
    -f, --force             Force migration even if database state looks problematic
    -c, --clean-deploy      Assume clean database deployment (skip some checks)
    --skip-static          Skip static files collection
    --skip-checks          Skip post-deployment checks

ENVIRONMENT VARIABLES:
    DATABASE_URL           Database connection string (required)
    SECRET_KEY            Django secret key (required)
    DJANGO_SETTINGS_MODULE Django settings module (required)
    STATIC_ROOT           Static files directory (optional)
    LOG_FILE              Log file path (default: /tmp/deployment.log)
    DEBUG                 Enable debug logging (default: false)
    FORCE_MIGRATION       Force migration despite warnings (default: false)

EXAMPLES:
    # Fresh deployment on empty database
    $SCRIPT_NAME --clean-deploy
    
    # Diagnose database state only
    $SCRIPT_NAME --diagnose
    
    # Force migration on problematic database
    $SCRIPT_NAME --force
    
    # Quick deployment without static files
    $SCRIPT_NAME --skip-static

EOF
}

# Database state diagnosis only
diagnose_only() {
    log_info "🔍 Database State Diagnosis Mode"
    
    if ! test_database_connection; then
        log_error "Cannot diagnose - database connection failed"
        exit 1
    fi
    
    diagnose_database_state
    local diagnosis_result=$?
    
    if [[ $diagnosis_result -eq 0 ]]; then
        log_info "✅ Database is ready for deployment"
    else
        log_warning "⚠️  Database may need attention before deployment"
        log_info "Consider using --force flag or cleaning the database"
    fi
    
    exit $diagnosis_result
}

# Main execution function
main() {
    local DIAGNOSE_ONLY=false
    local FORCE_MIGRATION=false
    local CLEAN_DEPLOY=false
    local SKIP_STATIC=false
    local SKIP_CHECKS=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--diagnose)
                DIAGNOSE_ONLY=true
                shift
                ;;
            -f|--force)
                FORCE_MIGRATION=true
                export FORCE_MIGRATION=true
                shift
                ;;
            -c|--clean-deploy)
                CLEAN_DEPLOY=true
                shift
                ;;
            --skip-static)
                SKIP_STATIC=true
                shift
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log_info "🚀 Starting production-grade deployment process..."
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Log file: ${LOG_FILE}"
    
    if [[ "$FORCE_MIGRATION" == "true" ]]; then
        log_warning "⚠️  FORCE_MIGRATION enabled - will proceed despite warnings"
    fi
    
    if [[ "$CLEAN_DEPLOY" == "true" ]]; then
        log_info "📦 Clean deployment mode - assuming fresh database"
    fi
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "${LOG_FILE}")"
    
    # Handle diagnose-only mode
    if [[ "$DIAGNOSE_ONLY" == "true" ]]; then
        diagnose_only
    fi
    
    # Execute deployment steps
    pre_deployment_checks
    execute_migrations
    
    if [[ "$SKIP_STATIC" != "true" ]]; then
        collect_static_files
    else
        log_info "📦 Skipping static files collection"
    fi
    
    if [[ "$SKIP_CHECKS" != "true" ]]; then
        post_deployment_checks
    else
        log_info "🔍 Skipping post-deployment checks"
    fi
    
    log_info "🎉 Deployment completed successfully!"
    log_info "Application is ready to serve traffic"
}

# Main execution function
main_legacy() {
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
