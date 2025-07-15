#!/bin/bash

cd /Users/guillermomartincorrea/Desktop/Repositorios_personales/nutrition-pro/crm-nutricion-pro

find apps -name "*.json" -path "*/fixtures/*" -type f -exec sed -i '' 's/"WHITE"/"PERSONAL"/g' {} \;
find apps -name "*.json" -path "*/fixtures/*" -type f -exec sed -i '' 's/"BLACK"/"BUSINESS"/g' {} \;
find fixtures -name "*.json" -type f -exec sed -i '' 's/"WHITE"/"PERSONAL"/g' {} \; 2>/dev/null || true
find fixtures -name "*.json" -type f -exec sed -i '' 's/"BLACK"/"BUSINESS"/g' {} \; 2>/dev/null || true

echo "✅ Fixtures updated"
