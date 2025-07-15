#!/bin/bash

# BACKUP
echo "=== BACKUP ==="
git add .
git commit -m "Pre-migration backup: white/black to personal/business"

# PYTHON FILES
echo "=== PYTHON FILES ==="
find apps/ -name "*.py" -type f -exec sed -i '' "s/'white'/'personal'/g" {} \;
find apps/ -name "*.py" -type f -exec sed -i '' "s/'black'/'business'/g" {} \;
find apps/ -name "*.py" -type f -exec sed -i '' 's/"white"/"personal"/g' {} \;
find apps/ -name "*.py" -type f -exec sed -i '' 's/"black"/"business"/g' {} \;
find apps/ -name "*.py" -type f -exec sed -i '' "s/'WHITE'/'PERSONAL'/g" {} \;
find apps/ -name "*.py" -type f -exec sed -i '' "s/'BLACK'/'BUSINESS'/g" {} \;
find apps/ -name "*.py" -type f -exec sed -i '' 's/"WHITE"/"PERSONAL"/g' {} \;
find apps/ -name "*.py" -type f -exec sed -i '' 's/"BLACK"/"BUSINESS"/g' {} \;

# HTML FILES
echo "=== HTML FILES ==="
find templates/ -name "*.html" -type f -exec sed -i '' "s/'white'/'personal'/g" {} \;
find templates/ -name "*.html" -type f -exec sed -i '' "s/'black'/'business'/g" {} \;
find templates/ -name "*.html" -type f -exec sed -i '' 's/"white"/"personal"/g' {} \;
find templates/ -name "*.html" -type f -exec sed -i '' 's/"black"/"business"/g' {} \;
find templates/ -name "*.html" -type f -exec sed -i '' "s/white|black/personal|business/g" {} \;

# URL PATTERNS
echo "=== URL PATTERNS ==="
find apps/ -name "urls.py" -type f -exec sed -i '' "s/white|black/personal|business/g" {} \;

# DISPLAY NAMES
echo "=== DISPLAY NAMES ==="
find . -name "*.py" -type f -exec sed -i '' "s/Servicios White/Servicios Personal/g" {} \;
find . -name "*.py" -type f -exec sed -i '' "s/Servicios Black/Servicios Business/g" {} \;
find . -name "*.html" -type f -exec sed -i '' "s/Servicios White/Servicios Personal/g" {} \;
find . -name "*.html" -type f -exec sed -i '' "s/Servicios Black/Servicios Business/g" {} \;

# FIXTURES
echo "=== FIXTURES ==="
find . -name "*.json" -type f -exec sed -i '' 's/"WHITE"/"PERSONAL"/g' {} \;
find . -name "*.json" -type f -exec sed -i '' 's/"BLACK"/"BUSINESS"/g' {} \;

echo "=== MIGRATION COMPLETE ==="
