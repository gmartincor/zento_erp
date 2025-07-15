#!/bin/bash

echo "🔄 Actualizando keys de diccionarios en templates..."

# Buscar todos los templates HTML
template_files=$(find templates -name "*.html" -type f)

for file in $template_files; do
    # Verificar si el archivo contiene las keys viejas
    if grep -q "white_services\|black_services\|white_revenue\|black_revenue\|white_percentage\|black_percentage" "$file"; then
        echo "  📝 Actualizando $file..."
        
        # Actualizar keys en templates
        sed -i '' \
            -e 's/white_services/personal_services/g' \
            -e 's/black_services/business_services/g' \
            -e 's/white_revenue/personal_revenue/g' \
            -e 's/black_revenue/business_revenue/g' \
            -e 's/white_percentage/personal_percentage/g' \
            -e 's/black_percentage/business_percentage/g' \
            "$file"
    fi
done

echo "✅ Keys de diccionarios actualizadas en templates"
