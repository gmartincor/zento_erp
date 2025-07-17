#!/bin/bash
# =============================================================================
# Script de verificación de longevidad del proyecto
# =============================================================================

set -e

echo "🔍 VERIFICANDO CONFIGURACIÓN DE LONGEVIDAD..."
echo "================================================"

# Verificar versiones críticas
echo "📦 Verificando versiones de dependencias..."

# Verificar Django
DJANGO_VERSION=$(python -c "import django; print(django.VERSION[:2])")
if [[ "$DJANGO_VERSION" == "(4, 2)" ]]; then
    echo "✅ Django 4.2 LTS - OK"
else
    echo "⚠️  Django no está en versión 4.2 LTS"
fi

# Verificar Python
PYTHON_VERSION=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    echo "✅ Python 3.12 - OK"
else
    echo "⚠️  Python no está en versión 3.12"
fi

# Verificar Node.js
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [[ "$NODE_VERSION" == "20" ]]; then
    echo "✅ Node.js 20 LTS - OK"
else
    echo "⚠️  Node.js no está en versión 20 LTS"
fi

# Verificar pip
PIP_VERSION=$(pip --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PIP_VERSION" == "24.0" ]]; then
    echo "✅ pip 24.0 - OK"
else
    echo "⚠️  pip no está en versión 24.0"
fi

echo ""
echo "🔐 Verificando configuraciones de seguridad..."

# Verificar SSL
if grep -q "SECURE_SSL_REDIRECT = True" config/settings/production.py; then
    echo "✅ SSL redirect - OK"
else
    echo "❌ SSL redirect no configurado"
fi

# Verificar HSTS
if grep -q "SECURE_HSTS_SECONDS = 63072000" config/settings/production.py; then
    echo "✅ HSTS 2 años - OK"
else
    echo "⚠️  HSTS no configurado para 2 años"
fi

echo ""
echo "📊 Estado del proyecto:"
echo "========================"

# Verificar si hay archivos con versiones flotantes
echo "🔍 Verificando versiones fijas..."

if grep -q "\^" package.json; then
    echo "❌ package.json tiene versiones flotantes (^)"
else
    echo "✅ package.json tiene versiones fijas"
fi

if grep -q "==" requirements.txt | grep -qv "pip==24.0"; then
    echo "✅ requirements.txt tiene versiones fijas"
else
    echo "⚠️  requirements.txt podría tener versiones flotantes"
fi

echo ""
echo "🏥 Verificando salud del sistema..."

# Verificar logs
if [ -f "/tmp/django.log" ]; then
    echo "✅ Archivo de logs existe"
    LOG_SIZE=$(du -h /tmp/django.log | cut -f1)
    echo "   Tamaño: $LOG_SIZE"
else
    echo "⚠️  Archivo de logs no encontrado"
fi

# Verificar static files
if [ -d "static_collected" ]; then
    echo "✅ Static files recolectados"
else
    echo "⚠️  Static files no recolectados (ejecutar collectstatic)"
fi

echo ""
echo "📅 Recordatorios de mantenimiento:"
echo "=================================="
echo "• Revisar logs mensualmente"
echo "• Backup de DB semanal"
echo "• Verificar certificados SSL cada 6 meses"
echo "• Evaluación de actualizaciones: enero 2026"
echo ""
echo "✅ Verificación completada!"
