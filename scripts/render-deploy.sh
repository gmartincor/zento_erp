#!/bin/bash
# =============================================================================
# render-deploy.sh - Script SIMPLE de deployment para Render
# =============================================================================

set -e

echo "🚀 Iniciando deployment en Render..."

# Limpiar datos de prueba
echo "🧹 Limpiando datos de prueba..."
python manage.py cleanup_production --confirm

# Aplicar migraciones
echo "🔄 Aplicando migraciones..."
python manage.py migrate_schemas --shared

# Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Inicializar configuración de producción
echo "⚙️ Inicializando configuración de producción..."
python manage.py init_production

echo "✅ Deployment completado exitosamente"

# Función para verificar variables de entorno críticas
check_environment() {
    log "🔍 Verificando variables de entorno..."
    
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
