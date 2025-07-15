#!/bin/bash

echo "🔍 VERIFICACIÓN MASIVA DE MIGRACIÓN..."

tenants=("tenant_sofia" "tenant_elena" "tenant_miguel" "tenant_patricia" "tenant_roberto2" "tenant_roberto" "tenant_laura" "ana_martinez" "carlos" "maria" "admin")

total_personal=0
total_business=0
total_services=0
problematic_tenants=0

for tenant in "${tenants[@]}"; do
    echo "📊 Verificando $tenant..."
    
    result=$(python manage.py tenant_command shell --schema="$tenant" -c "
from apps.accounting.models import ClientService
services = ClientService.objects.all()
personal_count = services.filter(category='personal').count()
business_count = services.filter(category='business').count()
old_categories = services.filter(category__in=['white', 'black', 'WHITE', 'BLACK']).count()
print(f'{services.count()},{personal_count},{business_count},{old_categories}')
" 2>/dev/null | tail -1)
    
    IFS=',' read -r total personal business old <<< "$result"
    
    if [ "$old" -gt 0 ]; then
        echo "  ⚠️  $tenant: $old servicios con categorías viejas!"
        ((problematic_tenants++))
    else
        echo "  ✅ $tenant: $total servicios (P:$personal, B:$business) ✓"
    fi
    
    ((total_services += total))
    ((total_personal += personal))
    ((total_business += business))
done

echo ""
echo "📈 RESUMEN FINAL:"
echo "  Total servicios: $total_services"
echo "  Personal: $total_personal"
echo "  Business: $total_business" 
echo "  Tenants problemáticos: $problematic_tenants"

if [ "$problematic_tenants" -eq 0 ]; then
    echo "🎉 MIGRACIÓN EXITOSA - Todos los tenants actualizados correctamente"
else
    echo "⚠️  REVISAR - Algunos tenants tienen problemas"
fi
