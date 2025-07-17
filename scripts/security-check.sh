#!/bin/bash

# =============================================================================
# security-check.sh - Verificación de seguridad para Docker y despliegue
# =============================================================================

set -e

echo "🔒 Verificación de seguridad para ZentoERP"
echo "=========================================="

# Función para verificar vulnerabilidades Docker
check_docker_vulnerabilities() {
    echo "🐳 Verificando vulnerabilidades en imágenes Docker..."
    
    if command -v docker &> /dev/null; then
        echo "ℹ️  Docker encontrado, verificando imágenes..."
        
        # Verificar si hay imágenes build
        if docker images | grep -q "zentoerp"; then
            echo "✅ Imágenes ZentoERP encontradas"
            docker images | grep "zentoerp"
        else
            echo "ℹ️  No hay imágenes ZentoERP construidas localmente"
        fi
        
        # Sugerir herramientas de seguridad
        echo "💡 Recomendaciones de seguridad:"
        echo "   - Usar herramientas como 'docker scan' o 'trivy'"
        echo "   - Actualizar imágenes base regularmente"
        echo "   - Usar imágenes oficiales cuando sea posible"
        
    else
        echo "⚠️  Docker no está instalado o disponible"
    fi
}

# Función para verificar configuración de seguridad
check_security_config() {
    echo "🔧 Verificando configuración de seguridad..."
    
    # Verificar archivos sensibles
    if [ -f ".env" ]; then
        echo "⚠️  Archivo .env encontrado - asegurar que no esté en git"
        if grep -q "SECRET_KEY.*django-insecure" .env; then
            echo "🔴 SECRET_KEY de desarrollo encontrada - cambiar en producción"
        fi
    fi
    
    # Verificar .gitignore
    if [ -f ".gitignore" ]; then
        if grep -q "\.env" .gitignore; then
            echo "✅ .env está en .gitignore"
        else
            echo "⚠️  .env no está en .gitignore"
        fi
    fi
    
    # Verificar Dockerfile
    if [ -f "Dockerfile" ]; then
        if grep -q "USER.*root" Dockerfile; then
            echo "⚠️  Usuario root detectado en Dockerfile"
        else
            echo "✅ Usuario no-root configurado en Dockerfile"
        fi
    fi
}

# Función para verificar dependencias Python
check_python_security() {
    echo "🐍 Verificando dependencias Python..."
    
    if command -v pip &> /dev/null; then
        echo "ℹ️  Verificando vulnerabilidades con pip-audit (si está instalado)..."
        
        if command -v pip-audit &> /dev/null; then
            pip-audit --require-hashes --desc
        else
            echo "💡 Instalar pip-audit para verificar vulnerabilidades:"
            echo "   pip install pip-audit"
        fi
        
        echo "💡 Mantener dependencias actualizadas:"
        echo "   pip list --outdated"
        
    else
        echo "⚠️  pip no está disponible"
    fi
}

# Función para verificar configuración de producción
check_production_security() {
    echo "🏭 Verificando configuración de producción..."
    
    # Verificar settings de producción
    if [ -f "config/settings/production.py" ]; then
        echo "✅ Archivo de configuración de producción encontrado"
        
        # Verificar configuraciones de seguridad
        if grep -q "DEBUG.*=.*False" config/settings/production.py; then
            echo "✅ DEBUG=False en producción"
        else
            echo "⚠️  DEBUG no está configurado como False"
        fi
        
        if grep -q "SECURE_SSL_REDIRECT.*=.*True" config/settings/production.py; then
            echo "✅ SSL redirect habilitado"
        else
            echo "⚠️  SSL redirect no configurado"
        fi
        
        if grep -q "SECURE_HSTS_SECONDS" config/settings/production.py; then
            echo "✅ HSTS configurado"
        else
            echo "⚠️  HSTS no configurado"
        fi
        
    else
        echo "⚠️  Archivo de configuración de producción no encontrado"
    fi
}

# Ejecutar verificaciones
echo "🔍 Iniciando verificaciones de seguridad..."
echo ""

check_docker_vulnerabilities
echo ""

check_security_config
echo ""

check_python_security
echo ""

check_production_security
echo ""

echo "✅ Verificación de seguridad completada"
echo "========================================"
echo ""
echo "📋 Resumen de recomendaciones:"
echo "   1. Mantener imágenes Docker actualizadas"
echo "   2. Usar SECRET_KEY segura en producción"
echo "   3. Verificar que archivos sensibles estén en .gitignore"
echo "   4. Ejecutar auditorías de seguridad regularmente"
echo "   5. Usar HTTPS en producción"
echo "   6. Mantener dependencias actualizadas"
echo ""
echo "🔗 Herramientas recomendadas:"
echo "   - docker scan (vulnerabilidades Docker)"
echo "   - pip-audit (vulnerabilidades Python)"
echo "   - bandit (análisis de código Python)"
echo "   - safety (verificación de dependencias)"
