#!/bin/bash

echo "🔄 ACTUALIZACIÓN MASIVA: Variables y keys restantes..."

# Lista de archivos a actualizar
files_to_update=(
    "apps/accounting/services/business_line_service.py"
    "apps/accounting/services/navigation_service.py"
    "apps/accounting/templatetags/accounting_tags.py"
    "apps/accounting/managers/business_line_manager.py"
    "apps/accounting/views/business_line.py"
)

for file in "${files_to_update[@]}"; do
    if [ -f "$file" ]; then
        echo "  📝 Actualizando $file..."
        
        # Actualizar todas las variables y keys
        sed -i '' \
            -e 's/white_count/personal_count/g' \
            -e 's/black_count/business_count/g' \
            -e 's/white_services/personal_services/g' \
            -e 's/black_services/business_services/g' \
            -e 's/white_revenue/personal_revenue/g' \
            -e 's/black_revenue/business_revenue/g' \
            -e "s/'WHITE'/'PERSONAL'/g" \
            -e "s/'BLACK'/'BUSINESS'/g" \
            "$file"
    else
        echo "  ⚠️  Archivo no encontrado: $file"
    fi
done

echo "✅ Actualización masiva completada"
