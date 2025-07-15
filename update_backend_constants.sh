#!/bin/bash

cd /Users/guillermomartincorrea/Desktop/Repositorios_personales/nutrition-pro/crm-nutricion-pro

find apps/accounting/services -name "*.py" -type f -exec sed -i '' "s/'white'/SERVICE_CATEGORIES['PERSONAL']/g" {} \;
find apps/accounting/services -name "*.py" -type f -exec sed -i '' "s/'black'/SERVICE_CATEGORIES['BUSINESS']/g" {} \;
find apps/accounting/services -name "*.py" -type f -exec sed -i '' "s/'WHITE'/SERVICE_CATEGORIES['PERSONAL']/g" {} \;
find apps/accounting/services -name "*.py" -type f -exec sed -i '' "s/'BLACK'/SERVICE_CATEGORIES['BUSINESS']/g" {} \;

find apps/accounting/templatetags -name "*.py" -type f -exec sed -i '' "s/'white'/SERVICE_CATEGORIES['PERSONAL']/g" {} \;
find apps/accounting/templatetags -name "*.py" -type f -exec sed -i '' "s/'black'/SERVICE_CATEGORIES['BUSINESS']/g" {} \;

find apps/accounting/views -name "*.py" -type f -exec sed -i '' "s/'WHITE'/SERVICE_CATEGORIES['PERSONAL']/g" {} \;
find apps/accounting/views -name "*.py" -type f -exec sed -i '' "s/'BLACK'/SERVICE_CATEGORIES['BUSINESS']/g" {} \;

find apps/tenants/management/commands -name "*.py" -type f -exec sed -i '' "s/'white'/SERVICE_CATEGORIES['PERSONAL']/g" {} \;
find apps/tenants/management/commands -name "*.py" -type f -exec sed -i '' "s/'black'/SERVICE_CATEGORIES['BUSINESS']/g" {} \;

echo "✅ Backend constants updated"
