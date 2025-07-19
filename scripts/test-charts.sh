#!/bin/bash

# =============================================================================
# SCRIPT DE VERIFICACIÓN DE CHARTS - ZENTOERP
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[CHARTS-TEST]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Verificar archivos JavaScript necesarios
check_js_files() {
    log "Verificando archivos JavaScript..."
    
    local files=(
        "static/js/chart.min.js"
        "static/js/dashboard/config.js" 
        "static/js/dashboard/utils.js"
        "static/js/dashboard/charts.js"
    )
    
    local missing=0
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            success "Encontrado: $file"
        else
            error "Falta: $file"
            ((missing++))
        fi
    done
    
    if [ $missing -eq 0 ]; then
        success "Todos los archivos JavaScript encontrados"
        return 0
    else
        error "Faltan $missing archivos JavaScript"
        return 1
    fi
}

# Verificar archivos estáticos compilados
check_collected_static() {
    log "Verificando archivos estáticos compilados..."
    
    if [ ! -d "static_collected" ]; then
        warn "Directorio static_collected no existe"
        return 1
    fi
    
    local files=(
        "static_collected/js/chart.min.js"
        "static_collected/js/dashboard/config.js"
        "static_collected/js/dashboard/utils.js" 
        "static_collected/js/dashboard/charts.js"
    )
    
    local missing=0
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            success "Compilado: $file"
        else
            error "Falta compilado: $file"
            ((missing++))
        fi
    done
    
    if [ $missing -eq 0 ]; then
        success "Todos los archivos JavaScript compilados encontrados"
        return 0
    else
        error "Faltan $missing archivos JavaScript compilados"
        return 1
    fi
}

# Verificar sintaxis de archivos JavaScript
check_js_syntax() {
    log "Verificando sintaxis de archivos JavaScript..."
    
    local files=(
        "static/js/dashboard/config.js"
        "static/js/dashboard/utils.js" 
        "static/js/dashboard/charts.js"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            if node -c "$file" 2>/dev/null; then
                success "Sintaxis OK: $file"
            else
                error "Error de sintaxis: $file"
                return 1
            fi
        fi
    done
    
    success "Sintaxis JavaScript válida"
}

# Verificar configuración de Django
check_django_config() {
    log "Verificando configuración de Django..."
    
    # Verificar STATIC_URL
    python manage.py shell -c "
from django.conf import settings
print('STATIC_URL:', settings.STATIC_URL)
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATICFILES_DIRS:', settings.STATICFILES_DIRS)
" || warn "No se pudo verificar configuración Django"
}

# Ejecutar collectstatic
run_collectstatic() {
    log "Ejecutando collectstatic..."
    python manage.py collectstatic --noinput --verbosity=2 || {
        error "Falló collectstatic"
        return 1
    }
    success "collectstatic completado"
}

# Verificar templates
check_templates() {
    log "Verificando templates..."
    
    if grep -q "chart.min.js" templates/base.html; then
        success "Chart.js referenciado en base.html"
    else
        error "Chart.js no referenciado en base.html"
    fi
    
    if grep -q "dashboard/config.js" templates/dashboard/home.html; then
        success "Dashboard config.js referenciado"
    else
        error "Dashboard config.js no referenciado"
    fi
}

# Función principal
main() {
    log "🚀 Iniciando verificación de charts..."
    
    check_js_files || exit 1
    check_js_syntax || exit 1
    check_templates || exit 1
    check_django_config
    run_collectstatic || exit 1
    check_collected_static || exit 1
    
    success "🎉 Verificación de charts completada exitosamente"
    log "📊 Los charts deberían funcionar correctamente en producción"
}

# Ejecutar si es llamado directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
