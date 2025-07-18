#!/bin/bash

# FRESH DATABASE SETUP FOR PRODUCTION
# Para cuando necesitamos empezar completamente desde cero
# DANGER: Este script borra TODA la data existente

set -euo pipefail

# Configuration
readonly LOG_FILE="${LOG_FILE:-/tmp/fresh_setup.log}"
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

log_warning "⚠️  FRESH DATABASE SETUP - THIS WILL DELETE ALL EXISTING DATA!"
log_info "Environment: $ENVIRONMENT"
log_info "Log file: $LOG_FILE"

cd "$(dirname "$0")/.."

# 1. Drop all tables (nuclear option)
log_warning "🗑️ Dropping all existing tables..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()

# Get all table names
cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'\")
tables = cursor.fetchall()

if tables:
    print(f'Found {len(tables)} tables to drop')
    for table in tables:
        table_name = table[0]
        print(f'Dropping table: {table_name}')
        cursor.execute(f'DROP TABLE IF EXISTS \"{table_name}\" CASCADE')
        
    connection.commit()
    print('All tables dropped successfully')
else:
    print('No tables found to drop')
" --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE"

# 2. Run fresh migrations
log_info "🚀 Running fresh migrations on clean database..."
python manage.py migrate_schemas --shared --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE"

# 3. Verify success
log_info "✅ Verifying fresh setup..."
python manage.py showmigrations --settings=config.settings.production 2>&1 | tee -a "$LOG_FILE"

log_info "✅ Fresh database setup completed successfully!"
