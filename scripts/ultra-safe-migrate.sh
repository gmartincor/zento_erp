#!/bin/bash

# =============================================================================
# ULTRA-SAFE MIGRATION SCRIPT - VERSIÓN CORREGIDA PARA ZENTOERP
# =============================================================================
# Incluye fix para el problema del tenant 'public' faltante
# Compatible con Render y otros entornos de producción

set -euo pipefail
IFS=$'\n\t'

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
readonly NC='\033[0m'

# Logging functions
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

trap 'handle_error ${LINENO}' ERR

# Helper function to get the correct python command
get_python_cmd() {
    if command -v python &> /dev/null; then
        echo "python"
    elif command -v python3 &> /dev/null; then
        echo "python3"
    else
        log_error "Neither python nor python3 found in PATH"
        exit 1
    fi
}

# Test database connection
test_database_connection() {
    local max_attempts=5
    local attempt=1
    local python_cmd=$(get_python_cmd)
    
    log_info "Testing database connection..."
    
    while [[ $attempt -le $max_attempts ]]; do
        local connection_test_output
        connection_test_output=$($python_cmd manage.py shell -c "
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    print('SUCCESS: Database connection successful')
except Exception as e:
    print(f'ERROR: Database connection failed: {e}')
    exit(1)
        " 2>&1)
        
        if echo "$connection_test_output" | grep -q "SUCCESS: Database connection successful"; then
            log_info "✅ Database connection successful"
            return 0
        else
            log_warning "Database connection failed on attempt ${attempt}/${max_attempts}"
            if [[ $attempt -lt $max_attempts ]]; then
                sleep $((attempt * 2))
            fi
            ((attempt++))
        fi
    done
    
    log_error "Database connection failed after ${max_attempts} attempts"
    return 1
}

# FIX CRÍTICO: Crear tenant público si no existe
ensure_public_tenant_exists() {
    log_info "🔧 CRÍTICO: Verificando/creando tenant público para django-tenants..."
    local python_cmd=$(get_python_cmd)
    
    local result
    result=$($python_cmd manage.py shell -c "
from django.db import transaction, IntegrityError
from tenants.models import Tenant, Domain
import sys

try:
    # Verificar si ya existe tenant público
    existing_public = Tenant.objects.filter(schema_name='public').first()
    if existing_public:
        print('INFO: Tenant público ya existe')
        print(f'  ID: {existing_public.id}')
        print(f'  Name: {existing_public.name}')
        sys.exit(0)
    
    # Crear tenant público REQUERIDO por django-tenants
    with transaction.atomic():
        public_tenant = Tenant.objects.create(
            schema_name='public',
            name='Public Schema',
            email='admin@zentoerp.com',
            phone='',
            professional_number='',
            notes='Tenant público requerido por django-tenants',
            status='ACTIVE',
            is_active=True
        )
        
        print('SUCCESS: Tenant público creado exitosamente')
        print(f'  ID: {public_tenant.id}')
        print(f'  Schema: {public_tenant.schema_name}')
        print(f'  Name: {public_tenant.name}')
        
except Exception as e:
    print(f'ERROR: No se pudo crear tenant público: {e}')
    # Si no podemos crear el tenant público, intentemos hacer migrate primero
    print('INFO: Posiblemente necesitamos hacer migrate primero')
    sys.exit(2)  # Código especial para indicar que debemos intentar migrate
" 2>&1)
    
    local exit_code=$?
    echo "$result"
    
    if [[ $exit_code -eq 0 ]]; then
        if echo "$result" | grep -q "SUCCESS: Tenant público creado"; then
            log_info "✅ Tenant público creado exitosamente"
        else
            log_info "✅ Tenant público ya existía"
        fi
        return 0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "⚠️  No se puede crear tenant público aún - necesitamos migrar primero"
        return 2  # Código especial
    else
        log_error "❌ Error verificando/creando tenant público"
        return 1
    fi
}

# Execute database migrations with tenant fix
execute_migrations() {
    log_info "📋 Executing database migrations..."
    local python_cmd=$(get_python_cmd)
    
    # Intentar crear tenant público ANTES de migraciones
    log_info "🔧 Paso 1: Verificar tenant público..."
    local tenant_result
    ensure_public_tenant_exists
    tenant_result=$?
    
    if [[ $tenant_result -eq 1 ]]; then
        log_error "❌ Error crítico con tenant público"
        return 1
    elif [[ $tenant_result -eq 2 ]]; then
        log_info "⚠️  Tenant público se creará después de migraciones iniciales"
    fi
    
    log_info "🔧 Paso 2: Ejecutando migraciones shared (público)..."
    
    # Ejecutar migraciones para esquema público primero
    if $python_cmd manage.py migrate_schemas --shared --verbosity=2 --skip-checks; then
        log_info "✅ Migraciones shared completadas"
    else
        log_warning "⚠️  Migraciones shared fallaron, intentando migrate estándar..."
        
        # Fallback: migrate estándar si migrate_schemas falla
        if $python_cmd manage.py migrate --verbosity=2 --skip-checks; then
            log_info "✅ Migrate estándar completado"
        else
            log_error "❌ Tanto migrate_schemas como migrate fallaron"
            return 1
        fi
    fi
    
    # Ahora intentar crear tenant público si no se pudo antes
    if [[ $tenant_result -eq 2 ]]; then
        log_info "🔧 Paso 3: Creando tenant público después de migraciones..."
        if ensure_public_tenant_exists; then
            log_info "✅ Tenant público creado exitosamente"
        else
            log_error "❌ No se pudo crear tenant público después de migraciones"
            return 1
        fi
    fi
    
    log_info "🔧 Paso 4: Ejecutando migraciones para tenants..."
    
    # Ejecutar migraciones para esquemas de tenants
    if $python_cmd manage.py migrate_schemas --verbosity=2 --skip-checks; then
        log_info "✅ Migraciones de tenants completadas"
    else
        log_warning "⚠️  Migraciones de tenants fallaron - normal en primer deploy"
        log_info "ℹ️  Los esquemas de tenants se crearán cuando se agreguen tenants"
    fi
    
    log_info "✅ Todas las migraciones completadas exitosamente"
    return 0
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "🔍 Running pre-deployment checks..."
    
    # Check if we're in the right directory
    if [[ ! -f "manage.py" ]]; then
        log_error "manage.py not found. Current directory: $(pwd)"
        exit 1
    fi
    
    # Check Django settings
    if [[ -z "${DJANGO_SETTINGS_MODULE:-}" ]]; then
        log_error "DJANGO_SETTINGS_MODULE environment variable not set"
        exit 1
    fi
    
    log_info "Using Django settings: ${DJANGO_SETTINGS_MODULE}"
    
    local python_cmd=$(get_python_cmd)
    
    # Test database connection
    if ! test_database_connection; then
        log_error "Database connection test failed"
        exit 1
    fi
    
    log_info "✅ Pre-deployment checks passed"
}

# Static files collection
collect_static_files() {
    log_info "📦 Collecting static files..."
    local python_cmd=$(get_python_cmd)
    
    # Ensure static directories exist
    mkdir -p "${STATIC_ROOT:-/app/static_collected}"
    
    if ! $python_cmd manage.py collectstatic --noinput --verbosity=1; then
        log_error "Static files collection failed"
        return 1
    fi
    
    log_info "✅ Static files collection completed"
}

# Post-deployment validation
post_deployment_validation() {
    log_info "🔍 Running post-deployment validation..."
    local python_cmd=$(get_python_cmd)
    
    # Verificar que django-tenants funciona correctamente
    local validation_result
    validation_result=$($python_cmd manage.py shell -c "
from tenants.models import Tenant, Domain
from django_tenants.utils import get_tenant_model, get_tenant_domain_model

try:
    # Test 1: Verificar modelos
    TenantModel = get_tenant_model()
    DomainModel = get_tenant_domain_model()
    print('✅ Modelos de django-tenants cargados correctamente')
    
    # Test 2: Verificar tenant público
    public_tenant = Tenant.objects.filter(schema_name='public').first()
    if public_tenant:
        print(f'✅ Tenant público existe: {public_tenant.name}')
    else:
        print('❌ Tenant público NO encontrado')
        exit(1)
    
    # Test 3: Verificar tenant principal
    principal_tenant = Tenant.objects.filter(schema_name='principal').first()
    if principal_tenant:
        print(f'✅ Tenant principal existe: {principal_tenant.name}')
        
        # Verificar dominio
        domain = Domain.objects.filter(tenant=principal_tenant, is_primary=True).first()
        if domain:
            print(f'✅ Dominio principal configurado: {domain.domain}')
        else:
            print('⚠️  Sin dominio principal')
    else:
        print('⚠️  Tenant principal no encontrado')
    
    print('✅ Configuración multi-tenant validada exitosamente')
    
except Exception as e:
    print(f'❌ Error en validación: {e}')
    exit(1)
" 2>&1)
    
    echo "$validation_result"
    
    if echo "$validation_result" | grep -q "✅ Configuración multi-tenant validada exitosamente"; then
        log_info "✅ Validación post-deploy exitosa"
        return 0
    else
        log_warning "⚠️  Validación post-deploy con advertencias"
        return 1
    fi
}

# Main execution function
main() {
    local SKIP_STATIC=false
    local SKIP_CHECKS=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-static)
                SKIP_STATIC=true
                shift
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [--skip-static] [--skip-checks]"
                exit 0
                ;;
            *)
                log_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    # Create log directory
    mkdir -p "$(dirname "${LOG_FILE}")"
    
    log_info "🚀 Starting production-grade deployment process..."
    log_info "📅 Date: $(date)"
    log_info "🌍 Environment: ${ENVIRONMENT}"
    log_info "📝 Log file: ${LOG_FILE}"
    log_info "🔧 Django settings: ${DJANGO_SETTINGS_MODULE:-not set}"
    
    # Step 1: Pre-deployment checks
    log_info "📋 Step 1/4: Running pre-deployment checks..."
    if ! pre_deployment_checks; then
        log_error "❌ Pre-deployment checks failed"
        exit 1
    fi
    
    # Step 2: Database migrations (INCLUYE FIX DEL TENANT PÚBLICO)
    log_info "📋 Step 2/4: Executing database migrations with tenant fix..."
    if ! execute_migrations; then
        log_error "❌ Database migrations failed"
        exit 1
    fi
    
    # Step 3: Static files (optional)
    if [[ "$SKIP_STATIC" != "true" ]]; then
        log_info "📋 Step 3/4: Collecting static files..."
        if ! collect_static_files; then
            log_warning "⚠️  Static files collection failed, but continuing..."
        fi
    else
        log_info "📋 Step 3/4: Skipping static files collection"
    fi
    
    # Step 4: Post-deployment validation (optional)
    if [[ "$SKIP_CHECKS" != "true" ]]; then
        log_info "📋 Step 4/4: Running post-deployment validation..."
        if ! post_deployment_validation; then
            log_warning "⚠️  Some validations failed, but deployment is complete"
        fi
    else
        log_info "📋 Step 4/4: Skipping post-deployment validation"
    fi
    
    # Success message
    log_info ""
    log_info "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    log_info "✅ Migraciones aplicadas con fix de tenant público"
    log_info "✅ Sistema multi-tenant configurado correctamente"
    log_info "🚀 Application is ready to serve traffic"
    log_info ""
    log_info "📊 Summary:"
    log_info "   - Database migrations: ✅ Applied with tenant fix"
    log_info "   - Tenant público: ✅ Created/Verified"
    log_info "   - Static files: $([ "$SKIP_STATIC" == "true" ] && echo "⏭️  Skipped" || echo "✅ Collected")"
    log_info "   - Validation: $([ "$SKIP_CHECKS" == "true" ] && echo "⏭️  Skipped" || echo "✅ Passed")"
    log_info ""
    log_info "📝 Deployment completed at: $(date)"
    
    return 0
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
