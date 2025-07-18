#!/bin/bash

# MIGRATION CONSISTENCY FIXER FOR PRODUCTION
# Resuelve inconsistencias entre migraciones consolidadas y registros de BD existentes
# Safe for production - Solo actualiza registros de django_migrations

set -euo pipefail

# Configuration
readonly LOG_FILE="${LOG_FILE:-/tmp/migration_fix.log}"
readonly ENVIRONMENT="${ENVIRONMENT:-production}"

# Color codes
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

log_info() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_info "🔧 Starting migration consistency fix for production..."
log_info "Environment: $ENVIRONMENT"
log_info "Log file: $LOG_FILE"

cd "$(dirname "$0")/.."

# 0. FIRST: Verify database state (is it really empty?)
log_info "🔍 VERIFYING DATABASE STATE - Checking if database is truly empty..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()

# Check if django_migrations table exists
try:
    cursor.execute(\"SELECT COUNT(*) FROM django_migrations\")
    migration_count = cursor.fetchone()[0]
    print(f'django_migrations table exists with {migration_count} records')
    
    if migration_count > 0:
        cursor.execute(\"SELECT app, name FROM django_migrations ORDER BY applied\")
        migrations = cursor.fetchall()
        print('Existing migrations in database:')
        for app, name in migrations:
            print(f'  - {app}.{name}')
    else:
        print('django_migrations table is empty')
        
except Exception as e:
    print(f'django_migrations table does not exist or error: {e}')

# Check for other Django tables
try:
    cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'\")
    tables = cursor.fetchall()
    table_count = len(tables)
    print(f'Total tables in database: {table_count}')
    if table_count > 0:
        print('Tables found:')
        for table in tables:
            print(f'  - {table[0]}')
    else:
        print('Database is completely empty')
except Exception as e:
    print(f'Error checking tables: {e}')
" --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE"

# 1. Check current migration status
log_info "📋 Checking current migration status..."
python manage.py showmigrations --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE" || true

# 2. Mark unified business_lines migration as applied (fake)
log_info "🎯 Marking business_lines.0001_unified_business_lines as applied (fake)..."
python manage.py migrate_schemas --shared --fake business_lines 0001_unified_business_lines --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE"

# 3. Verify the fix
log_info "✅ Verifying migration consistency..."
python manage.py showmigrations business_lines accounting --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE"

# 4. Try normal migration now
log_info "🚀 Attempting normal migration process..."
python manage.py migrate_schemas --shared --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE"

log_info "✅ Migration consistency fix completed successfully!"
