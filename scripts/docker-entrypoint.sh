#!/bin/bash
# =============================================================================
# docker-entrypoint.sh - Script de entrada para contenedores ZentoERP
# =============================================================================

set -e  # Salir si algún comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Función para esperar que PostgreSQL esté listo
wait_for_postgres() {
    local host=${DB_HOST:-localhost}
    local port=${DB_PORT:-5432}
    local user=${DB_USER:-postgres}
    local db=${DB_NAME:-zentoerp}
    
    log "🔄 Esperando que PostgreSQL esté disponible en ${host}:${port}..."
    
    # Verificar que podemos conectarnos a la base de datos específica usando Python
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if python -c "import psycopg2; psycopg2.connect(host='$host', port='$port', user='$user', password='$DB_PASSWORD', database='$db')" 2>/dev/null; then
            log "✅ PostgreSQL está listo y accesible!"
            return 0
        fi
        
        warn "Esperando acceso a base de datos. Intento $((attempts + 1))/30..."
        sleep 2
        attempts=$((attempts + 1))
    done
    
    error "No se pudo conectar a PostgreSQL después de 30 intentos"
    return 1
}

# Función para esperar que Redis esté listo (si está configurado)
wait_for_redis() {
    if [ -n "$REDIS_URL" ]; then
        log "🔄 Verificando conexión a Redis..."
        
        # Extraer host y puerto de REDIS_URL si es necesario
        local redis_host=$(echo $REDIS_URL | sed 's|redis://||' | cut -d: -f1)
        local redis_port=$(echo $REDIS_URL | sed 's|redis://||' | cut -d: -f2 | cut -d/ -f1)
        
        # Usar valores por defecto si no se pueden extraer
        redis_host=${redis_host:-redis}
        redis_port=${redis_port:-6379}
        
        while ! redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1; do
            warn "Redis no está listo. Reintentando en 2 segundos..."
            sleep 2
        done
        
        log "✅ Redis está listo!"
    fi
}

# Función para aplicar migraciones
apply_migrations() {
    log "📦 Aplicando migraciones de django-tenants..."
    
    # Aplicar migraciones compartidas primero
    log "🔄 Aplicando migraciones compartidas (public schema)..."
    python manage.py migrate_schemas --shared
    
    # Aplicar migraciones de tenants
    log "🔄 Aplicando migraciones de tenants..."
    python manage.py migrate_schemas
    
    log "✅ Todas las migraciones aplicadas correctamente"
}

# Función para recolectar archivos estáticos
collect_static() {
    log "📁 Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
    log "✅ Archivos estáticos recolectados"
}

# Función para verificar la configuración
check_configuration() {
    log "🔍 Verificando configuración de Django..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        log "🏥 Ejecutando verificaciones de deploy para producción..."
        python manage.py check --deploy
    else
        python manage.py check
    fi
    
    log "✅ Configuración verificada"
}

# Función para inicializar datos si es necesario
initialize_data() {
    local environment=${ENVIRONMENT:-development}
    
    if [ "$environment" = "production" ]; then
        log "🚀 Inicializando configuración de producción..."
        python manage.py init_production --skip-migrate --skip-collectstatic || warn "Error en inicialización de producción"
    else
        log "📊 Usando datos existentes (desarrollo con BD sincronizada). No se cargan fixtures."
    fi
}

# Función para crear directorios necesarios
create_directories() {
    log "📂 Creando directorios necesarios..."
    
    # Crear directorio de logs
    mkdir -p /app/logs
    
    # Crear directorio de media
    mkdir -p /app/media
    
    # Crear directorio de static_collected
    mkdir -p /app/static_collected
    
    log "✅ Directorios creados"
}

# Función principal de inicialización
initialize() {
    log "🚀 Iniciando ZentoERP..."
    log "📊 Entorno: ${ENVIRONMENT:-development}"
    log "🐍 Django Settings: ${DJANGO_SETTINGS_MODULE}"
    
    # Crear directorios
    create_directories
    
    # Esperar servicios externos
    wait_for_postgres
    wait_for_redis
    
    # Verificar configuración
    check_configuration
    
    # Aplicar migraciones
    apply_migrations
    
    # Recolectar archivos estáticos
    collect_static
    
    # Inicializar datos si es necesario
    initialize_data
    
    log "✅ Inicialización completada"
}

# Función para modo desarrollo
run_development() {
    log "🔧 Iniciando servidor de desarrollo..."
    exec python manage.py runserver 0.0.0.0:8000
}

# Función para modo producción
run_production() {
    log "🌟 Iniciando servidor de producción con Gunicorn..."
    exec gunicorn \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-3} \
        --worker-class ${GUNICORN_WORKER_CLASS:-sync} \
        --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
        --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
        --timeout ${GUNICORN_TIMEOUT:-30} \
        --keep-alive ${GUNICORN_KEEPALIVE:-2} \
        --log-level ${GUNICORN_LOG_LEVEL:-info} \
        --access-logfile ${GUNICORN_ACCESS_LOG:--} \
        --error-logfile ${GUNICORN_ERROR_LOG:--} \
        config.wsgi:application
}

# Script principal
main() {
    # Si se pasan argumentos, ejecutarlos directamente
    if [ $# -gt 0 ]; then
        log "🔧 Ejecutando comando personalizado: $@"
        exec "$@"
    fi
    
    # Inicialización común
    initialize
    
    # Decidir qué servidor ejecutar basado en el entorno
    if [ "$ENVIRONMENT" = "production" ]; then
        run_production
    else
        run_development
    fi
}

# Ejecutar función principal con todos los argumentos
main "$@"
