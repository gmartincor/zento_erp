#!/bin/bash
# =============================================================================
# setup.sh - Script SIMPLE de configuración para desarrolladores
# =============================================================================

set -e

echo "🚀 Configurando ZentoERP..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ ERROR: manage.py no encontrado. Ejecuta desde el directorio raíz del proyecto"
    exit 1
fi

# Crear .env desde .env.example si no existe
if [ ! -f ".env" ]; then
    echo "📝 Creando .env desde .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita .env con tu configuración específica"
fi

# Crear virtual environment si no existe
if [ ! -d "venv" ]; then
    echo "🐍 Creando virtual environment..."
    python3 -m venv venv
fi

# Activar virtual environment
echo "🔄 Activando virtual environment..."
source venv/bin/activate

# Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Instalar dependencias Node.js
echo "📦 Instalando dependencias Node.js..."
npm ci

# Compilar CSS
echo "🎨 Compilando CSS..."
npm run build-css

# Crear directorio de logs
mkdir -p logs

echo "✅ Configuración completada"
echo ""
echo "🎯 SIGUIENTES PASOS:"
echo "1. Edita .env con tu configuración"
echo "2. Ejecuta: source venv/bin/activate"
echo "3. Ejecuta: python manage.py runserver"
echo "4. O usa Docker: make dev"
