# 🐳 Guía de Docker para ZentoERP

## 📋 Opciones de Desarrollo

### **OPCIÓN 1: Desarrollo tradicional (RECOMENDADO para desarrollo diario)**
```bash
# Configurar entorno
make setup-env          # Crea .env desde .env.example
make install-deps       # Instala dependencias Python
make install-node       # Instala dependencias Node.js

# Desarrollo diario
make css-build          # Compilar CSS
python manage.py runserver  # Servidor Django
```

### **OPCIÓN 2: Desarrollo con Docker (RECOMENDADO para testing)**
```bash
# Comando simple con Makefile
make dev                # Desarrollo básico (PostgreSQL + App)
make full-dev           # Desarrollo completo (PostgreSQL + Redis + App)
make dev-tools          # Con TailwindCSS watcher

# Comandos equivalentes sin Makefile
docker-compose --profile dev up
docker-compose --profile full-dev up
docker-compose --profile dev --profile dev-tools up
```

### **OPCIÓN 3: Producción con Docker**
```bash
# Con variables de entorno configuradas
make prod              # Producción completa
make prod-daemon       # Producción en background

# Comando equivalente
docker-compose --profile prod up
```

## 🎯 Perfiles Disponibles

| Perfil | Servicios | Uso | Comando |
|--------|-----------|-----|---------|
| `dev` | PostgreSQL + App | Desarrollo básico | `make dev` |
| `full-dev` | PostgreSQL + Redis + App | Desarrollo completo | `make full-dev` |
| `prod` | Redis + App | Producción | `make prod` |
| `dev-tools` | TailwindCSS watcher | Herramientas de desarrollo | `make dev-tools` |

## 🛠️ Comandos Útiles (Makefile)

### **Desarrollo**
```bash
make help              # Ver todos los comandos disponibles
make dev               # Iniciar desarrollo básico
make full-dev          # Iniciar desarrollo completo
make dev-tools         # Iniciar con herramientas de desarrollo
```

### **CSS y Frontend**
```bash
make css-build         # Compilar CSS para producción
make css-watch         # Compilar CSS en modo watch
```

### **Base de Datos**
```bash
make migrate           # Aplicar migraciones
make makemigrations    # Crear migraciones
make shell             # Acceder a shell de Django
make dbshell           # Acceder a shell de PostgreSQL
```

### **Testing y Calidad**
```bash
make test              # Ejecutar tests
make test-coverage     # Tests con coverage
make lint              # Ejecutar linting
make format            # Formatear código
```

### **Construcción y Limpieza**
```bash
make build             # Rebuild todas las imágenes
make build-dev         # Rebuild solo desarrollo
make build-prod        # Rebuild solo producción
make clean             # Limpiar contenedores
make clean-all         # Limpiar todo (incluyendo imágenes)
```

### **Logs y Estado**
```bash
make logs              # Ver logs de la aplicación
make logs-db           # Ver logs de PostgreSQL
make logs-redis        # Ver logs de Redis
make status            # Ver estado de servicios
make health            # Verificar health de la aplicación
```

### **Deployment**
```bash
make deploy-render     # Deploy a Render.com
make init-prod         # Inicializar producción
make cleanup-prod      # Limpiar datos de prueba
```

## � Inicio Rápido

### **Setup Inicial (Una sola vez)**
```bash
# Clonar y configurar proyecto
git clone <tu-repo>
cd crm-nutricion-pro
./scripts/setup.sh       # Configura todo automáticamente
```

### **Desarrollo Diario**
```bash
# Opción 1: Tradicional
source venv/bin/activate
python manage.py runserver

# Opción 2: Con Docker
make dev                 # Más fácil y consistente
```

## 🔧 Configuración de Entorno

### **Archivos de Configuración**
```
├── .env.example         # Plantilla base
├── .env.development     # Configuración para desarrollo
├── .env.defaults        # Valores por defecto para Docker
├── .env                 # Tu configuración personal (no versionada)
└── .env.production      # Configuración para producción
```

### **Variables de Entorno Importantes**
```bash
# Obligatorias
SECRET_KEY=tu-secret-key-aqui
DATABASE_URL=postgres://usuario:password@host:port/db

# Opcionales para desarrollo
DEBUG=True
LOAD_TEST_DATA=True
REDIS_URL=redis://localhost:6379/0
```

## 🐳 Docker Compose Profiles

### **Arquitectura de Servicios**
```yaml
# Profile: dev
services:
  - postgres (Puerto 5433)
  - app-dev (Puerto 8000)

# Profile: full-dev
services:
  - postgres (Puerto 5433)
  - redis (Puerto 6380)
  - app-dev (Puerto 8000)

# Profile: prod
services:
  - redis (Puerto 6380)
  - app-prod (Puerto 8000)
```

### **Configuración Avanzada**
```bash
# Variables de entorno para Docker
export COMPOSE_PROJECT_NAME=zentoerp_dev
export APP_PORT_EXTERNAL=8000
export DB_PORT_EXTERNAL=5433

# Usar configuración específica
docker-compose --env-file .env.development --profile dev up
```

## 🔍 Troubleshooting

### **¿TailwindCSS no compila?**
```bash
# Verificar Node.js
node --version
npm --version

# Reinstalar dependencias
npm ci

# Compilar manualmente
npm run build-css
```

### **¿Base de datos no conecta?**
```bash
# Verificar que PostgreSQL está corriendo
brew services list | grep postgres

# En Docker
docker-compose ps
```

### **¿Redis es necesario?**
- **Desarrollo**: NO es necesario
- **Producción**: SÍ es recomendado para cache

## 🚀 Deployment

### **Preparación para Producción**
```bash
# 1. Limpiar datos de prueba
python manage.py cleanup_production --confirm

# 2. Inicializar producción
python manage.py init_production

# 3. Build Docker para producción
docker-compose -f docker-compose.prod.yml up --build
```

### **Health Check**
```bash
# Verificar estado de la aplicación
curl http://localhost:8000/health/

# En producción
curl https://zentoerp.com/health/
```

## 📦 Estructura de Archivos

```
├── Dockerfile                    # Multi-stage build optimizado
├── docker-compose.yml           # Configuración unificada con profiles
├── Makefile                     # Comandos simplificados
├── .env.example                 # Plantilla de configuración
├── .env.development             # Configuración para desarrollo
├── .env.defaults                # Valores por defecto
├── .gitignore                   # Archivos excluidos del control de versiones
├── scripts/
│   ├── setup.sh                 # Script de configuración inicial
│   ├── docker-entrypoint.sh     # Inicialización de contenedores
│   └── render-deploy.sh         # Deploy a Render
├── requirements.txt             # Dependencias Python
├── requirements-dev.txt         # Dependencias de desarrollo
├── package.json                 # Dependencias Node.js
└── DOCKER_GUIDE.md             # Esta guía
```

## 🔒 Seguridad y Mejores Prácticas

### **Contenedores**
- ✅ Usuario no-root en contenedores
- ✅ Multi-stage build para imágenes pequeñas
- ✅ Health checks para monitoring
- ✅ Límites de recursos en producción
- ✅ Redes aisladas con subredes específicas

### **Variables de Entorno**
- ✅ Separación por entornos
- ✅ .env no versionado
- ✅ Valores por defecto seguros
- ✅ Validación de variables críticas

### **Desarrollo**
- ✅ Makefile para comandos consistentes
- ✅ Scripts de setup automatizados
- ✅ Linting y formateo automático
- ✅ Tests con coverage
- ✅ Logs estructurados

## 🎯 Recomendaciones Finales

### **Para Desarrollo Diario**
1. **Usa el setup automático**: `./scripts/setup.sh`
2. **Usa Makefile**: `make dev` en lugar de comandos largos
3. **Mantén el entorno limpio**: `make clean` regularmente
4. **Ejecuta tests**: `make test` antes de commits

### **Para Producción**
1. **Usa Docker siempre**: `make prod`
2. **Configura variables de entorno**: En Render dashboard
3. **Monitorea health**: `/health/` endpoint
4. **Limpia datos de prueba**: `make cleanup-prod`

### **Para el Equipo**
1. **Documentación actualizada**: Mantén esta guía actualizada
2. **Versionado semántico**: Para releases
3. **Code review**: Obligatorio para cambios de infraestructura
4. **Backup regular**: De base de datos y configuraciones
