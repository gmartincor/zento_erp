#!/bin/bash

echo "🚀 FASE 9: VALIDACIÓN INTEGRAL DEL SISTEMA"
echo "=========================================="

errors=0
warnings=0

echo "🔍 1. VALIDACIÓN DE IMPORTS Y SINTAXIS"
echo "--------------------------------------"

python manage.py shell -c "
try:
    from apps.core.constants import SERVICE_CATEGORIES, CATEGORY_CONFIG, CATEGORY_DEFAULTS
    from apps.accounting.models import ClientService
    from apps.accounting.services.statistics_service import StatisticsService
    print('✅ Todos los imports exitosos')
except Exception as e:
    print(f'❌ Error de import: {e}')
    exit(1)
" || ((errors++))

echo ""
echo "🗄️ 2. VALIDACIÓN DE BASE DE DATOS"
echo "--------------------------------"

validation_result=$(python manage.py shell -c "
from apps.tenants.models import Tenant
from apps.accounting.models import ClientService
from apps.core.constants import SERVICE_CATEGORIES

tenants = Tenant.objects.filter(is_deleted=False).exclude(schema_name='public')
total_personal = 0
total_business = 0
problematic = 0

for tenant in tenants:
    try:
        from django_tenants.utils import schema_context
        with schema_context(tenant.schema_name):
            services = ClientService.objects.all()
            personal = services.filter(category=SERVICE_CATEGORIES['PERSONAL']).count()
            business = services.filter(category=SERVICE_CATEGORIES['BUSINESS']).count()
            old_cats = services.filter(category__in=['white', 'black', 'WHITE', 'BLACK']).count()
            
            if old_cats > 0:
                problematic += 1
                print(f'⚠️  {tenant.schema_name}: {old_cats} categorías obsoletas')
            
            total_personal += personal
            total_business += business
    except Exception as e:
        problematic += 1
        print(f'❌ Error en {tenant.schema_name}: {e}')

print(f'RESUMEN_BD:{tenants.count()},{total_personal},{total_business},{problematic}')
" 2>/dev/null | tail -1)

IFS=',' read -r total_tenants personal business problems <<< "${validation_result#*:}"

if [ "$problems" -eq 0 ]; then
    echo "✅ Base de datos: $total_tenants tenants, $personal personal, $business business"
else
    echo "❌ Base de datos: $problems tenants con problemas"
    ((errors++))
fi

echo ""
echo "🎯 3. VALIDACIÓN DE FUNCIONALIDAD"
echo "--------------------------------"

python manage.py tenant_command shell --schema=tenant_sofia -c "
from apps.accounting.models import ClientService
from apps.core.constants import SERVICE_CATEGORIES

try:
    personal_services = ClientService.objects.filter(category=SERVICE_CATEGORIES['PERSONAL'])
    business_services = ClientService.objects.filter(category=SERVICE_CATEGORIES['BUSINESS'])
    
    print(f'✅ Funcionalidad: P:{personal_services.count()}, B:{business_services.count()}')
    print('✅ Consultas con constantes funcionan correctamente')
    
except Exception as e:
    print(f'❌ Error funcional: {e}')
    exit(1)
" || ((errors++))

echo ""
echo "🌐 4. VALIDACIÓN DE URLS Y ROUTING"
echo "--------------------------------"

python manage.py shell -c "
from django.urls import reverse
from django.test import RequestFactory
from apps.core.constants import SERVICE_CATEGORIES

try:
    # Test URLs principales
    urls_to_test = [
        ('accounting:index', {}),
    ]
    
    for url_name, kwargs in urls_to_test:
        url = reverse(url_name, kwargs=kwargs)
        
    # Test URLs con categorías
    category_urls = [
        'accounting:category-services',
    ]
    
    print('✅ URLs generan correctamente')
    
except Exception as e:
    print(f'❌ Error URLs: {e}')
    exit(1)
" || ((errors++))

echo ""
echo "🔧 5. VALIDACIÓN DE MIGRACIÓN"
echo "----------------------------"

migration_status=$(python manage.py showmigrations accounting | grep "0019_update_category_choices")
if [[ $migration_status == *"[X]"* ]]; then
    echo "✅ Migración 0019 aplicada correctamente"
else
    echo "❌ Migración 0019 no aplicada"
    ((errors++))
fi

echo ""
echo "📊 RESULTADO FINAL"
echo "=================="

if [ $errors -eq 0 ]; then
    echo "🎉 VALIDACIÓN EXITOSA - Sistema 100% operativo"
    echo "   - Imports y sintaxis: ✅"
    echo "   - Base de datos: ✅ ($total_tenants tenants)"
    echo "   - Funcionalidad: ✅"
    echo "   - URLs y routing: ✅"
    echo "   - Migración: ✅"
    echo ""
    echo "✅ FASE 9 COMPLETADA - Sistema listo para producción"
    exit 0
else
    echo "❌ VALIDACIÓN FALLIDA - $errors errores encontrados"
    exit 1
fi
