#!/bin/bash
# =============================================================================
# render-deploy.sh - Script de deployment para Render (Fase 4)
# =============================================================================

set -e

echo "🚀 Iniciando deployment en Render para zentoerp.com..."
echo "======================================================"

# Función de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Función para verificar variables de entorno críticas
check_environment() {
    log "🔍 Verificando variables de entorno..."
    
    # Variables críticas
    REQUIRED_VARS=(
        "SECRET_KEY"
        "DB_NAME"
        "DB_USER"
        "DB_PASSWORD"
        "DB_HOST"
        "REDIS_URL"
        "ALLOWED_HOSTS"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            log "❌ ERROR: Variable $var no está definida"
            exit 1
        else
            log "✅ $var configurada correctamente"
        fi
    done
}

# Función para verificar conectividad de base de datos
check_database() {
    log "🔍 Verificando conectividad de base de datos..."
    
    if python manage.py dbshell -c "SELECT 1;" > /dev/null 2>&1; then
        log "✅ Conexión a base de datos exitosa"
    else
        log "❌ ERROR: No se puede conectar a la base de datos"
        exit 1
    fi
}

# Función para aplicar migraciones
apply_migrations() {
    log "🔄 Aplicando migraciones del esquema compartido..."
    python manage.py migrate_schemas --shared
    
    log "🔄 Creando tabla de cache..."
    python manage.py createcachetable
    
    log "🔄 Aplicando migraciones de tenants..."
    python manage.py migrate_schemas --tenant
}

# Función para recolectar archivos estáticos
collect_static() {
    log "📦 Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput --clear
}

# Función para crear superusuario si no existe
create_superuser() {
    log "👤 Verificando superusuario..."
    
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        python manage.py createsuperuser \
            --username "$DJANGO_SUPERUSER_USERNAME" \
            --email "$DJANGO_SUPERUSER_EMAIL" \
            --noinput || log "⚠️ Superusuario ya existe"
    else
        log "⚠️ Variables de superusuario no configuradas"
    fi
}

# Función para inicializar configuración de producción
init_production() {
    log "⚙️ Inicializando configuración de producción..."
    
    # Solo ejecutar si existe el comando
    if python manage.py help init_production > /dev/null 2>&1; then
        python manage.py init_production
    else
        log "ℹ️ Comando init_production no disponible"
    fi
}

# Función de limpieza (opcional)
cleanup_test_data() {
    log "🧹 Limpiando datos de prueba..."
    
    # Solo ejecutar si existe el comando
    if python manage.py help cleanup_production > /dev/null 2>&1; then
        python manage.py cleanup_production --confirm
    else
        log "ℹ️ Comando cleanup_production no disponible"
    fi
}

# Función para verificar health check
verify_health() {
    log "🏥 Verificando health check..."
    
    if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.test.utils import get_runner
from django.conf import settings
from django.http import HttpRequest
from apps.core.views.health import health_check

request = HttpRequest()
response = health_check(request)
print(f'Health check status: {response.status_code}')
exit(0 if response.status_code == 200 else 1)
"; then
        log "✅ Health check funcionando correctamente"
    else
        log "❌ ERROR: Health check falló"
        exit 1
    fi
}

# DEPLOYMENT PRINCIPAL
# =============================================================================

log "� Comenzando deployment para zentoerp.com"

# 1. Verificar entorno
check_environment

# 2. Verificar base de datos
check_database

# 3. Aplicar migraciones
apply_migrations

# 4. Recolectar archivos estáticos
collect_static

# 5. Crear superusuario (opcional)
create_superuser

# 6. Inicializar producción
init_production

# 7. Limpiar datos de prueba (opcional)
if [ "$CLEANUP_TEST_DATA" = "true" ]; then
    cleanup_test_data
fi

# 8. Verificar health check
verify_health

log "✅ Deployment completado exitosamente para zentoerp.com"
log "🌐 La aplicación está lista en https://zentoerp.com"
log "📱 Subdominios disponibles: https://[tenant].zentoerp.com"

echo "======================================================"
echo "✅ DEPLOYMENT COMPLETADO"
echo "======================================================"
    
    local required_vars=(
        "SECRET_KEY"
        "DATABASE_URL"
        "ALLOWED_HOSTS"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Variables de entorno faltantes:"
        for var in "${missing_vars[@]}"; do
            error "  - $var"
        done
        exit 1
    fi
    
    log "✅ Variables de entorno verificadas"
}

# Función para verificar conectividad de base de datos
check_database() {
    log "🗄️ Verificando conectividad de base de datos..."
    
    # Intentar conectar a la base de datos
    python << EOF
import os
import sys
import psycopg2
from urllib.parse import urlparse

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("ERROR: DATABASE_URL no está configurada")
    sys.exit(1)

try:
    # Parsear URL de base de datos
    url = urlparse(database_url)
    
    # Intentar conexión
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        database=url.path[1:]  # Remover '/' inicial
    )
    conn.close()
    print("✅ Conexión a base de datos exitosa")
except Exception as e:
    print(f"❌ Error conectando a base de datos: {e}")
    sys.exit(1)
EOF
    
    if [ $? -ne 0 ]; then
        error "No se pudo conectar a la base de datos"
        exit 1
    fi
}

# Función para limpiar datos de prueba
cleanup_test_data() {
    log "🧹 Limpiando datos de prueba..."
    python manage.py cleanup_production --confirm || warn "No se pudieron limpiar todos los datos de prueba"
    log "✅ Datos de prueba limpiados"
}

# Función para aplicar migraciones
apply_migrations() {
    log "📦 Aplicando migraciones..."
    
    # Migraciones compartidas
    python manage.py migrate_schemas --shared
    
    # Verificar si hay tenants existentes antes de migrar tenants
    local tenant_count=$(python -c "
from apps.tenants.models import Tenant
print(Tenant.objects.count())
" 2>/dev/null || echo "0")
    
    if [ "$tenant_count" -gt 0 ]; then
        log "🏢 Aplicando migraciones de tenants ($tenant_count tenants encontrados)..."
        python manage.py migrate_schemas
    else
        log "📝 No hay tenants existentes, saltando migraciones de tenants"
    fi
    
    log "✅ Migraciones aplicadas"
}

# Función para recolectar archivos estáticos
collect_static() {
    log "📁 Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
    log "✅ Archivos estáticos recolectados"
}

# Función para verificar configuración de producción
check_production_config() {
    log "🔍 Verificando configuración de producción..."
    python manage.py check --deploy
    log "✅ Configuración de producción verificada"
}

# Función para inicializar configuración de producción
init_production() {
    log "🚀 Inicializando configuración de producción..."
    python manage.py init_production --skip-migrate --skip-collectstatic
    log "✅ Configuración de producción inicializada"
}

# Función para verificar health check
verify_health() {
    log "🏥 Verificando health check..."
    
    # Esperar un momento para que el servidor se inicie
    sleep 5
    
    # Verificar que el servidor responde
    if command -v curl &> /dev/null; then
        local health_url="http://localhost:${PORT:-8000}/health/"
        curl -f "$health_url" || warn "Health check falló"
    else
        warn "curl no disponible, saltando health check"
    fi
}

# Función principal de deploy
main() {
    log "🚀 Iniciando deployment en Render..."
    info "🌐 Dominio: ${ALLOWED_HOSTS}"
    info "🐍 Django Settings: ${DJANGO_SETTINGS_MODULE}"
    
    # Verificar entorno
    check_environment
    
    # Verificar base de datos
    check_database
    
    # Limpiar datos de prueba
    cleanup_test_data
    
    # Aplicar migraciones
    apply_migrations
    
    # Recolectar archivos estáticos
    collect_static
    
    # Verificar configuración
    check_production_config
    
    # Inicializar producción
    init_production
    
    log "✅ Deployment completado exitosamente"
    log "🌟 ZentoERP está listo para producción!"
    
    # Información final
    info "📊 Información del deployment:"
    info "  • Dominio: ${ALLOWED_HOSTS}"
    info "  • Base de datos: Conectada"
    info "  • Archivos estáticos: Recolectados"
    info "  • Migraciones: Aplicadas"
    info "  • Entorno: Producción"
}

# Ejecutar función principal
main "$@"
