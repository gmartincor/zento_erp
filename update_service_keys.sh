#!/bin/bash

echo "🔄 Actualizando keys de diccionarios en servicios de accounting..."

# Buscar archivos de servicios
service_files=(
    "apps/accounting/services/history_service.py"
    "apps/accounting/services/business_line_service.py"
    "apps/accounting/services/navigation_service.py"
    "apps/accounting/services/statistics_service.py"
)

for file in "${service_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  📝 Actualizando $file..."
        
        # Actualizar keys en agregations y diccionarios
        sed -i '' \
            -e 's/white_services=/personal_services=/g' \
            -e 's/black_services=/business_services=/g' \
            -e 's/white_revenue=/personal_revenue=/g' \
            -e 's/black_revenue=/business_revenue=/g' \
            -e 's/white_percentage=/personal_percentage=/g' \
            -e 's/black_percentage=/business_percentage=/g' \
            -e "s/'white_services':/'personal_services':/g" \
            -e "s/'black_services':/'business_services':/g" \
            -e "s/'white_revenue':/'personal_revenue':/g" \
            -e "s/'black_revenue':/'business_revenue':/g" \
            -e "s/'white_percentage':/'personal_percentage':/g" \
            -e "s/'black_percentage':/'business_percentage':/g" \
            -e "s/\['white_services'\]/['personal_services']/g" \
            -e "s/\['black_services'\]/['business_services']/g" \
            -e "s/\['white_revenue'\]/['personal_revenue']/g" \
            -e "s/\['black_revenue'\]/['business_revenue']/g" \
            -e "s/\['white_percentage'\]/['personal_percentage']/g" \
            -e "s/\['black_percentage'\]/['business_percentage']/g" \
            -e "s/\.get('white_services')/\.get('personal_services')/g" \
            -e "s/\.get('black_services')/\.get('business_services')/g" \
            -e "s/\.get('white_revenue')/\.get('personal_revenue')/g" \
            -e "s/\.get('black_revenue')/\.get('business_revenue')/g" \
            -e "s/\.get('white_percentage')/\.get('personal_percentage')/g" \
            -e "s/\.get('black_percentage')/\.get('business_percentage')/g" \
            "$file"
    else
        echo "  ⚠️  Archivo no encontrado: $file"
    fi
done

echo "✅ Keys de diccionarios actualizadas en servicios"
