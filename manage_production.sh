#!/bin/bash
# =============================================================================
# manage_production.sh - Script para gestionar producción de forma segura
# =============================================================================

set -e  # Salir si hay algún error

echo "🚀 ZENTOERP - Gestión de Producción"
echo "=================================="

# Verificar que existe el archivo .env.production
if [ ! -f .env.production ]; then
    echo "❌ Error: No se encontró .env.production"
    echo "   Crea el archivo con las credenciales de producción"
    exit 1
fi

# Función para mostrar ayuda
show_help() {
    echo "Comandos disponibles:"
    echo ""
    echo "🔧 GESTIÓN DE USUARIOS:"
    echo "  create-superuser     - Crear un superusuario (interactivo)"
    echo "  create-tenant        - Crear tenant completo con usuario y dominio"
    echo "  list-users           - Listar todos los usuarios"
    echo "  set-password         - Cambiar contraseña de un usuario"
    echo ""
    echo "📊 INFORMACIÓN:"
    echo "  debug-tenants        - Ver información de tenants y dominios"
    echo "  show-domains         - Mostrar dominios configurados"
    echo "  migrate              - Aplicar migraciones"
    echo ""
    echo "Ejemplo: ./manage_production.sh create-superuser"
}

# Exportar variables de entorno desde .env.production
export $(grep -v '^#' .env.production | xargs)

case "$1" in
    "create-superuser")
        echo "👑 Creando superusuario para administración..."
        echo "⚠️  Este usuario tendrá acceso completo al sistema"
        echo ""
        echo "💡 RECOMENDACIONES:"
        echo "   - Username: admin, guillermo, o tu nombre preferido"
        echo "   - Email: tu email real (para recuperación)"
        echo "   - Password: mínimo 8 caracteres, usa algo seguro"
        echo ""
        read -p "¿Continuar? (y/n): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            python manage.py create_admin_user --tenant public
        else
            echo "❌ Operación cancelada"
        fi
        ;;
    
    "create-tenant")
        echo "🏥 Creando tenant completo..."
        echo "Este comando crea: tenant + dominio + usuario + migraciones"
        echo ""
        read -p "Schema name (ej: carlos, maria): " schema_name
        read -p "Nombre del nutricionista: " tenant_name
        read -p "Email: " email
        read -p "Username (Enter = usar schema): " username
        read -p "Dominio (ej: carlos.zentoerp.com): " domain
        read -s -p "Password (Enter = changeme123): " password
        echo ""
        
        # Usar defaults si están vacíos
        username=${username:-$schema_name}
        password=${password:-changeme123}
        
        python manage.py create_nutritionist_tenant \
            "$schema_name" \
            "$domain" \
            "$tenant_name" \
            "$email" \
            --username "$username" \
            --password "$password"
        ;;
    
    "list-users")
        echo "👥 Listando usuarios del sistema..."
        python manage.py shell -c "
from apps.authentication.models import User
from apps.tenants.models import Tenant
print('=== SUPERUSUARIOS ===')
for user in User.objects.filter(is_superuser=True):
    print(f'👑 {user.username} ({user.email}) - Tenant: {user.tenant.name if user.tenant else \"Sin tenant\"}')

print('\n=== USUARIOS DE TENANTS ===')
for user in User.objects.filter(tenant__isnull=False):
    print(f'👤 {user.username} ({user.email}) - Tenant: {user.tenant.name}')
    
print('\n=== TENANTS CONFIGURADOS ===')
for tenant in Tenant.objects.filter(is_deleted=False):
    print(f'🏥 {tenant.name} ({tenant.schema_name}) - Status: {tenant.status}')
"
        ;;
    
    "set-password")
        echo "🔑 Cambiar contraseña de usuario..."
        read -p "Username: " username
        python manage.py set_passwords --username "$username"
        ;;
    
    "debug-tenants")
        echo "🔍 Información de tenants y dominios..."
        python manage.py debug_tenants
        ;;
    
    "show-domains")
        echo "🌐 Dominios configurados..."
        python manage.py shell -c "
from apps.tenants.models import Domain
for domain in Domain.objects.all():
    print(f'{domain.domain} -> {domain.tenant.name} ({domain.tenant.schema_name}) - Primario: {domain.is_primary}')
"
        ;;
    
    "migrate")
        echo "📦 Aplicando migraciones..."
        python manage.py migrate_schemas --shared
        python manage.py migrate_schemas
        ;;
    
    "shell")
        echo "🐍 Abriendo shell de Django..."
        python manage.py shell
        ;;
    
    *)
        show_help
        ;;
esac
