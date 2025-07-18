#!/bin/bash

# Script simple para probar la conexión a la base de datos
# Útil para debug antes del despliegue

set -euo pipefail

# Verificar que estemos en el directorio correcto
if [[ ! -f "manage.py" ]]; then
    echo "Error: Este script debe ejecutarse desde el directorio raíz del proyecto Django"
    exit 1
fi

echo "🔍 Probando conexión a la base de datos..."
echo "📋 Variables de entorno:"
echo "  - DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-'no configurado'}"
echo "  - DATABASE_URL: $([ -n "${DATABASE_URL:-}" ] && echo "configurado" || echo "no configurado")"

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "⚠️  DATABASE_URL no está configurado"
    echo "📝 Variables individuales:"
    echo "  - DB_NAME: ${DB_NAME:-'no configurado'}"
    echo "  - DB_USER: ${DB_USER:-'no configurado'}"
    echo "  - DB_HOST: ${DB_HOST:-'no configurado'}"
    echo "  - DB_PORT: ${DB_PORT:-'no configurado'}"
fi

echo ""
echo "🧪 Ejecutando prueba de conexión..."

python manage.py shell -c "
from django.db import connection
from django.conf import settings
import os

print('=== Información de Configuración ===')
print(f'Settings module: {os.environ.get(\"DJANGO_SETTINGS_MODULE\", \"no configurado\")}')
print(f'Engine: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
print(f'Name/Database: {settings.DATABASES[\"default\"].get(\"NAME\", \"no configurado\")}')
print(f'Host: {settings.DATABASES[\"default\"].get(\"HOST\", \"no configurado\")}')
print(f'Port: {settings.DATABASES[\"default\"].get(\"PORT\", \"no configurado\")}')
print(f'User: {settings.DATABASES[\"default\"].get(\"USER\", \"no configurado\")}')

print('\n=== Probando Conexión ===')
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT version()')
        db_version = cursor.fetchone()[0]
        print(f'✅ Conexión exitosa!')
        print(f'📊 Versión de PostgreSQL: {db_version}')
        
        # Probar que django-tenants funcione
        cursor.execute('SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s', ['public'])
        result = cursor.fetchone()
        if result:
            print('✅ Schema público encontrado - django-tenants compatible')
        else:
            print('⚠️  Schema público no encontrado')
            
except Exception as e:
    print(f'❌ Error de conexión: {e}')
    print(f'🔧 Parámetros de conexión: {connection.settings_dict}')
    exit(1)

print('\n🎉 ¡Prueba completada exitosamente!')
"

echo ""
echo "✅ Prueba de conexión completada"
echo "💡 Si funcionó aquí, debería funcionar en el despliegue"
