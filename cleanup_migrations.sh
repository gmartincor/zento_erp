#!/bin/bash

# 🧹 SCRIPT DE LIMPIEZA Y REORGANIZACIÓN DE MIGRACIONES
# ====================================================
# Este script mueve las migraciones antiguas a backup y deja solo las unificadas

set -euo pipefail

echo "🚀 Iniciando limpieza de migraciones..."

# Crear directorios de backup si no existen
mkdir -p backups/migrations/old_tenants
mkdir -p backups/migrations/old_authentication  
mkdir -p backups/migrations/old_business_lines

# TENANTS - Mover migraciones antiguas
echo "📦 Moviendo migraciones antiguas de tenants..."
if ls apps/tenants/migrations/0*.py 2>/dev/null | grep -v "0001_unified_tenant_domain.py" | grep -v "__init__.py"; then
    ls apps/tenants/migrations/0*.py | grep -v "0001_unified_tenant_domain.py" | xargs -I {} mv {} backups/migrations/old_tenants/
fi

# AUTHENTICATION - Mover migraciones antiguas
echo "📦 Moviendo migraciones antiguas de authentication..."
if ls apps/authentication/migrations/0*.py 2>/dev/null | grep -v "0001_unified_user_tenant.py" | grep -v "__init__.py"; then
    ls apps/authentication/migrations/0*.py | grep -v "0001_unified_user_tenant.py" | xargs -I {} mv {} backups/migrations/old_authentication/
fi

# BUSINESS_LINES - Mover migraciones antiguas  
echo "📦 Moviendo migraciones antiguas de business_lines..."
if ls apps/business_lines/migrations/0*.py 2>/dev/null | grep -v "0001_unified_business_lines.py" | grep -v "__init__.py"; then
    ls apps/business_lines/migrations/0*.py | grep -v "0001_unified_business_lines.py" | xargs -I {} mv {} backups/migrations/old_business_lines/
fi

# Remover la migración consolidada problemática que creé antes
if [ -f "apps/tenants/migrations/0004_consolidated_tenant_final.py" ]; then
    echo "🗑️  Removiendo migración consolidada anterior..."
    mv apps/tenants/migrations/0004_consolidated_tenant_final.py backups/migrations/old_tenants/
fi

echo "✅ Limpieza completada!"
echo ""
echo "📋 Estado actual de migraciones:"
echo "TENANTS:"
ls -la apps/tenants/migrations/
echo ""
echo "AUTHENTICATION:"  
ls -la apps/authentication/migrations/
echo ""
echo "BUSINESS_LINES:"
ls -la apps/business_lines/migrations/
echo ""
echo "📁 Backups guardados en: backups/migrations/"
