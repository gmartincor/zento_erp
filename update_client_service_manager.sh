#!/bin/bash

echo "🔄 Actualizando client_service_manager.py..."

file="apps/accounting/managers/client_service_manager.py"

if [ -f "$file" ]; then
    echo "  📝 Actualizando $file..."
    
    # Actualizar todas las variables y keys
    sed -i '' \
        -e 's/white_services/personal_services/g' \
        -e 's/black_services/business_services/g' \
        -e 's/white_revenue/personal_revenue/g' \
        -e 's/black_revenue/business_revenue/g' \
        -e "s/'white'/'personal'/g" \
        -e "s/'black'/'business'/g" \
        "$file"
        
    echo "✅ client_service_manager.py actualizado"
else
    echo "  ⚠️  Archivo no encontrado: $file"
fi
