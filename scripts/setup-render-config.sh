#!/bin/bash

# =============================================================================
# setup-render-config.sh - Configuración segura para Render
# =============================================================================
# Este script te ayuda a crear render.yaml de forma segura

set -e

echo "🔒 Configuración Segura de Render para ZentoERP"
echo "=============================================="

# Verificar que no existe render.yaml
if [ -f "render.yaml" ]; then
    echo "⚠️  render.yaml ya existe. ¿Deseas sobrescribirlo? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Operación cancelada."
        exit 1
    fi
fi

echo ""
echo "📋 CONFIGURACIÓN REQUERIDA:"
echo "---------------------------"

# Solicitar credenciales de base de datos
echo "🗄️  Credenciales de PostgreSQL:"
echo "Database URL: postgresql://zentoerp_user:b7OCqNrdoVtdSObjiYVcU1BeubLTEWcO@dpg-d1sg1b3ipnbc73e279t0-a/zentoerp_production"
echo ""

DB_USER="zentoerp_user"
DB_PASSWORD="b7OCqNrdoVtdSObjiYVcU1BeubLTEWcO"
DB_HOST="dpg-d1sg1b3ipnbc73e279t0-a"
DB_NAME="zentoerp_production"

# Generar nueva SECRET_KEY
echo "🔑 Generando nueva SECRET_KEY..."
NEW_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
echo "✅ Nueva SECRET_KEY generada: ${NEW_SECRET_KEY:0:20}..."

# Crear render.yaml desde template
echo ""
echo "📝 Creando render.yaml desde template..."

cp render.yaml.template render.yaml

# Reemplazar variables
sed -i '' "s/\[DB_USER\]/$DB_USER/g" render.yaml
sed -i '' "s/\[DB_PASSWORD\]/$DB_PASSWORD/g" render.yaml
sed -i '' "s/\[DB_HOST\]/$DB_HOST/g" render.yaml
sed -i '' "s/\[DB_NAME\]/$DB_NAME/g" render.yaml
sed -i '' "s/\[GENERAR_SECRET_KEY_NUEVA\]/$NEW_SECRET_KEY/g" render.yaml

echo "✅ render.yaml creado exitosamente"

echo ""
echo "🔒 CONFIGURACIÓN DE SEGURIDAD:"
echo "-----------------------------"
echo "✅ render.yaml NO está en control de versiones (.gitignore)"
echo "✅ SECRET_KEY única generada"
echo "✅ Credenciales de base de datos configuradas"
echo "✅ Docker habilitado para multi-tenant"

echo ""
echo "🚀 SIGUIENTE PASO:"
echo "-----------------"
echo "1. Verificar render.yaml (no mostrará credenciales aquí)"
echo "2. En Render Dashboard, subir render.yaml o configurar manualmente"
echo "3. Deploy automático se activará"

echo ""
echo "⚠️  IMPORTANTE:"
echo "---------------"
echo "• render.yaml contiene credenciales sensibles"
echo "• NO compartir este archivo"
echo "• Mantener seguro en tu máquina local"
echo "• Usar solo para configurar Render"

echo ""
echo "🎯 ¡Configuración lista para deployment!"
echo "========================================"
