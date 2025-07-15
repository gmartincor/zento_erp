#!/bin/bash

cd /Users/guillermomartincorrea/Desktop/Repositorios_personales/nutrition-pro/crm-nutricion-pro

find templates -name "*.html" -type f -exec sed -i '' "s/category='white'/category='personal'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/category=\"white\"/category=\"personal\"/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/category='black'/category='business'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/category=\"black\"/category=\"business\"/g" {} \;

find templates -name "*.html" -type f -exec sed -i '' "s/== 'white'/== 'personal'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/== \"white\"/== \"personal\"/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/== 'black'/== 'business'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/== \"black\"/== \"business\"/g" {} \;

find templates -name "*.html" -type f -exec sed -i '' "s/'WHITE'/'PERSONAL'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/\"WHITE\"/\"PERSONAL\"/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/'BLACK'/'BUSINESS'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/\"BLACK\"/\"BUSINESS\"/g" {} \;

find templates -name "*.html" -type f -exec sed -i '' "s/== 'WHITE'/== 'PERSONAL'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/== \"WHITE\"/== \"PERSONAL\"/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/== 'BLACK'/== 'BUSINESS'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/== \"BLACK\"/== \"BUSINESS\"/g" {} \;

find templates -name "*.html" -type f -exec sed -i '' "s/filters.category == 'white'/filters.category == 'personal'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/filters.category == 'black'/filters.category == 'business'/g" {} \;

find templates -name "*.html" -type f -exec sed -i '' "s/current_category == 'white'/current_category == 'personal'/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/current_category == 'black'/current_category == 'business'/g" {} \;

find templates -name "*.html" -type f -exec sed -i '' "s/value=\"white\"/value=\"personal\"/g" {} \;
find templates -name "*.html" -type f -exec sed -i '' "s/value=\"black\"/value=\"business\"/g" {} \;

echo "✅ Templates updated"
