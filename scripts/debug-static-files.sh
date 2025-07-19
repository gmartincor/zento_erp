#!/bin/bash

# Script simplificado para verificar archivos estáticos en multi-tenant

echo "🔍 === VERIFICACIÓN ARCHIVOS ESTÁTICOS ==="
echo ""

echo "📁 Verificando archivos clave..."
files=(
    "static/js/chart.min.js"
    "static/js/dashboard/config.js" 
    "static/js/dashboard/utils.js"
    "static/js/dashboard/charts.js"
)

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file - NO ENCONTRADO"
    fi
done

echo ""
echo "🔧 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo ""
echo "✅ Verificación completada."
echo "💡 Si persisten problemas 404, verifica:"
echo "   1. Orden del middleware en settings"
echo "   2. Cache del navegador (Ctrl+F5)"
echo "   3. Configuración de DNS/subdominios"
