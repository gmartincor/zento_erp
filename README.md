# Zento ERP - Multi-Tenant Business Management System

A comprehensive ERP system designed for multi-tenant business management with hierarchical business lines, professional invoicing, and complete data portability.

## 🚀 Key Features

### 🏢 **Multi-Tenant Architecture**
- Complete tenant isolation using PostgreSQL schemas
- Secure multi-client management
- Independent data and configurations per tenant

### 👥 **Client & Service Management**
- Advanced client management with soft-delete protection
- Service categorization (PERSONAL/BUSINESS)
- Automated payment tracking and remainder management
- Client service lifecycle management

### 🏗️ **Hierarchical Business Lines**
- Up to 3-level business structure
- Dynamic business line management
- Revenue and client analytics per business line
- Flexible business organization

### 💰 **Professional Invoicing System**
- Complete invoice generation with PDF support
- Multi-company invoice management
- Professional invoice templates
- Invoice item management with tax calculations

### 💸 **Expense Management**
- Categorized expense tracking
- Monthly and yearly expense analytics
- Receipt attachment support
- Business expense reporting

### 📊 **Data Export & Portability**
- **Complete data portability system** with 4 export formats:
  - **CSV**: Professional tabular format with section headers
  - **Excel**: Multi-sheet workbooks with professional styling
  - **ZIP**: Individual CSV files per data type
  - **JSON**: Structured data for API integration
- Tenant-level data export with metadata
- Professional export interface integrated in navigation

### 🎛️ **Advanced Dashboard**
- Real-time business metrics
- Revenue and expense analytics
- Client and service overview
- Business performance indicators

## 🏗️ System Architecture

### Applications Structure

```
apps/
├── authentication/     # User authentication and management
├── tenants/           # Multi-tenant configuration and models  
├── core/              # Core utilities and export system
│   ├── exporters/     # Data export engines (CSV, Excel, ZIP, JSON)
│   ├── services/      # Export registry and serialization
│   └── management/    # Production management commands
├── accounting/        # Client and service management
├── business_lines/    # Hierarchical business structure
├── invoicing/         # Professional invoicing system
├── expenses/          # Expense tracking and categorization
└── dashboard/         # Analytics and reporting dashboard
```

## 🛠️ Technology Stack

- **Backend**: Django 4.2 LTS (Long Term Support)
- **Database**: PostgreSQL 12+ with schema-based multi-tenancy
- **Multi-tenancy**: django-tenants 3.8.0
- **Export System**: openpyxl 3.1.2 for Excel generation
- **PDF Generation**: ReportLab 4.0.7
- **Production**: Gunicorn + WhiteNoise
- **Frontend**: Django Templates with Alpine.js components

## 📋 Requirements

- Python 3.8+
- PostgreSQL 12+
- Docker (recommended for development)

## 🚀 Quick Start

### Development with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/gmartincor/zento_erp.git
   cd zento_erp
   ```

2. **Start with Docker**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Main application: http://localhost:8001
   - Admin interface: http://localhost:8001/admin

### Manual Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database**
   ```bash
   createdb zento_erp
   cp .env.example .env
   # Edit .env with your database configuration
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate_schemas
   ```

5. **Create superuser**
   ```bash
   python manage.py create_tenant_superuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

## 🔧 Production Deployment

### Using Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Production Setup

1. **Set production environment**
   ```bash
   export DJANGO_SETTINGS_MODULE=config.settings.production
   ```

2. **Initialize production**
   ```bash
   python manage.py check_production_ready
   python manage.py init_production
   ```

3. **Start with Gunicorn**
   ```bash
   gunicorn config.wsgi:application --config gunicorn.conf.py
   ```

## 📊 Data Export System

The system includes a comprehensive data portability solution:

### Export Formats
- **CSV**: Single file with section headers (`=== TABLE_NAME ===`)
- **Excel**: Multi-sheet workbook with professional styling
- **ZIP**: Individual CSV files compressed
- **JSON**: Structured data with metadata

### Export Coverage
- Client information and statistics
- Service details and payment history
- Business line hierarchy and analytics
- Company and invoice data
- Expense categories and records
- Tenant configuration and metadata

### Usage
Access via navigation menu → "Export Data" → Select format → Download

## 🧪 Management Commands

```bash
# Production readiness check
python manage.py check_production_ready

# Initialize production environment
python manage.py init_production

# Verify production setup
python manage.py verify_production

# Reset migrations (development only)
python manage.py reset_migrations_after_sync
```

## 📁 Project Structure

```
zento_erp/
├── apps/                   # Django applications
├── config/                 # Project configuration
├── templates/              # Global templates
├── static/                 # Static files
├── media/                  # User uploaded files
├── scripts/                # Deployment scripts
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker development setup
├── Dockerfile             # Container configuration
└── manage.py              # Django management script
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Repository**: https://github.com/gmartincor/zento_erp
- **Issues**: https://github.com/gmartincor/zento_erp/issues
- **Releases**: https://github.com/gmartincor/zento_erp/releases

---

**Developed with ❤️ for modern business management**
