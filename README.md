# Zento ERP

Sistema ERP para gestión integral de recursos empresariales con múltiples líneas de negocio.

## Características

- Gestión de clientes con soft-delete
- Líneas de negocio jerárquicas (hasta 3 niveles)
- Servicios de clientes con categorización PERSONAL/BUSINESS
- Sistema de remanentes para categoría BUSINESS
- Control de gastos por categorías
- Interfaz de administración avanzada

## Requisitos

- Python 3.8+
- PostgreSQL 12+

## Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/gmartincor/zento_erp.git
   cd zento_erp
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En macOS/Linux
   # o
   venv\Scripts\activate     # En Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar base de datos**
   - Crear base de datos PostgreSQL:
     ```bash
     createdb crm_nutricion_pro
     ```
   
   - Copiar archivo de configuración:
     ```bash
     cp .env.example .env
     ```
   
   - Editar `.env` con tus datos de base de datos

5. **Ejecutar migraciones**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Cargar datos iniciales**
   ```bash
   python manage.py loaddata apps/business_lines/fixtures/business_lines.json
   python manage.py loaddata apps/expenses/fixtures/expense_categories.json
   ```

7. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

8. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

## Estructura del Proyecto

```
zento-erp/
├── apps/
│   ├── core/           # Modelos base abstractos
│   ├── authentication/ # Sistema de usuarios personalizado
│   ├── business_lines/ # Líneas de negocio jerárquicas
│   ├── accounting/     # Clientes y servicios
│   └── expenses/       # Control de gastos
├── config/             # Configuración del proyecto
└── requirements.txt    # Dependencias
```

## Configuración de Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=crm_nutricion_pro
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password_postgres
DB_HOST=localhost
DB_PORT=5432
```

## Acceso al Admin

Una vez configurado, accede al panel de administración en:
http://127.0.0.1:8000/admin/

## Líneas de Negocio

El sistema incluye una estructura jerárquica predefinida:

- **Nivel 1**: Jaen, Glow, Rubi
- **Nivel 2**: NPV, PEPE (bajo Jaen), Dani-Rubi, Dani, Rubi (bajo Glow), Presencial, Online (bajo Rubi)
- **Nivel 3**: PEPE-normal, PEPE-videoCall (bajo PEPE)

## Sistema de Remanentes

- Solo aplicable a servicios de categoría BUSINESS
- Cada línea de negocio tiene su tipo específico de remanente:
  - PEPE-normal → remanente_pepe
  - PEPE-videoCall → remanente_pepe_video
  - Dani-Rubi → remanente_dani
  - Dani → remanente_aven
