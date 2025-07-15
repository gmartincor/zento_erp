#!/bin/bash

echo "🔄 Actualizando variables dinámicas en business_line.py..."

file="apps/accounting/views/business_line.py"

if [ -f "$file" ]; then
    echo "  📝 Actualizando $file..."
    
    # Actualizar asignaciones de atributos dinámicos
    sed -i '' \
        -e 's/current_line\.white_revenue/current_line.personal_revenue/g' \
        -e 's/current_line\.black_revenue/current_line.business_revenue/g' \
        -e 's/current_line\.white_services/current_line.personal_services/g' \
        -e 's/current_line\.black_services/current_line.business_services/g' \
        -e 's/white_revenue =/personal_revenue =/g' \
        -e 's/black_revenue =/business_revenue =/g' \
        -e 's/white_services =/personal_services =/g' \
        -e 's/black_services =/business_services =/g' \
        -e "s/'white_revenue':/'personal_revenue':/g" \
        -e "s/'black_revenue':/'business_revenue':/g" \
        -e "s/'white_services':/'personal_services':/g" \
        -e "s/'black_services':/'business_services':/g" \
        "$file"
    
    echo "✅ Variables dinámicas actualizadas en business_line.py"
else
    echo "  ⚠️  Archivo no encontrado: $file"
fi
