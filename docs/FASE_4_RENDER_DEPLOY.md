# 🚀 FASE 4: Configuración de Render y Deploy

## 📋 Guía Paso a Paso para Configurar Render

### **PASO 1: Preparar el Repositorio**

1. **Commit y Push de cambios:**
```bash
git add .
git commit -m "Fase 4: Configuración para deploy en Render"
git push origin production
```

2. **Verificar archivos esenciales:**
```bash
# Verificar que estos archivos existan:
ls -la Dockerfile
ls -la requirements.txt
ls -la scripts/render-deploy.sh
ls -la config/settings/production.py
```

### **PASO 2: Crear Servicios en Render**

#### **2.1 Crear Base de Datos PostgreSQL**

1. **Ir a Render Dashboard** → **New** → **PostgreSQL**
2. **Configuración:**
   - **Name**: `zentoerp-postgres`
   - **Database**: `zentoerp_production`
   - **User**: `zentoerp_user`
   - **Region**: `Oregon` (o más cercano a tus usuarios)
   - **Plan**: `Starter` ($7/mes)

3. **Obtener credenciales:**
   - Guardar: `Host`, `Port`, `Database`, `Username`, `Password`
   - URL de conexión completa también disponible

#### **2.2 Crear Cache Redis**

1. **Ir a Render Dashboard** → **New** → **Redis**
2. **Configuración:**
   - **Name**: `zentoerp-redis`
   - **Region**: `Oregon` (mismo que PostgreSQL)
   - **Plan**: `Starter` ($7/mes)

3. **Obtener URL de conexión:**
   - Ejemplo: `redis://red-xxxxx:6379`

#### **2.3 Crear Web Service**

1. **Ir a Render Dashboard** → **New** → **Web Service**
2. **Conectar repositorio:**
   - **GitHub**: Autorizar y seleccionar `crm-nutricion-pro`
   - **Branch**: `production`

3. **Configuración básica:**
   - **Name**: `zentoerp-web`
   - **Region**: `Oregon`
   - **Branch**: `production`
   - **Runtime**: `Docker`
   - **Plan**: `Starter` ($7/mes)

4. **Build & Deploy:**
   - **Build Command**: `./scripts/render-deploy.sh`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### **PASO 3: Configurar Variables de Entorno**

En el **Web Service** → **Environment**:

```bash
# Django Core
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your-generated-secret-key-here-50-characters-minimum
DEBUG=False
ENVIRONMENT=production
LOAD_TEST_DATA=False

# Domain Configuration
TENANT_DOMAIN=zentoerp.com
ALLOWED_HOSTS=zentoerp.com,*.zentoerp.com

# Database (usar valores de PostgreSQL creado)
DB_NAME=zentoerp_production
DB_USER=zentoerp_user
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
DB_PORT=5432

# Redis (usar URL de Redis creado)
REDIS_URL=redis://red-xxxxx:6379

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@zentoerp.com

# Static Files
STATIC_ROOT=/app/static_collected
MEDIA_ROOT=/app/media

# Logging
LOG_FILE=/tmp/django.log
LOG_LEVEL=WARNING

# Optional: Superuser
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@zentoerp.com
DJANGO_SUPERUSER_PASSWORD=your-admin-password

# Cleanup
CLEANUP_TEST_DATA=true
```

### **PASO 4: Configurar Dominio Personalizado**

1. **En el Web Service** → **Settings** → **Custom Domains**
2. **Agregar dominios:**
   - `zentoerp.com`
   - `*.zentoerp.com` (wildcard)

3. **Configurar DNS** (en tu proveedor de dominio):
```
A     @     → [IP que proporciona Render]
CNAME *     → zentoerp.com
CNAME www   → zentoerp.com
```

### **PASO 5: Primer Deploy**

1. **Hacer deploy:**
   - Render iniciará automáticamente el build
   - Monitoreará logs en tiempo real

2. **Verificar logs:**
   - Ver que migraciones se apliquen correctamente
   - Verificar que health check funcione
   - Confirmar que archivos estáticos se recolecten

### **PASO 6: Configurar SSL/TLS**

1. **SSL automático:**
   - Render configura automáticamente SSL
   - Certificados Let's Encrypt
   - Renovación automática

2. **Verificar SSL:**
   - Probar `https://zentoerp.com`
   - Probar `https://test.zentoerp.com`

### **PASO 7: Verificación Final**

1. **Health Check:**
```bash
curl -I https://zentoerp.com/health/
# Debe retornar 200 OK
```

2. **Subdominios:**
```bash
curl -I https://nutricion.zentoerp.com/
# Debe retornar 200 OK (después de crear tenant)
```

3. **Admin Panel:**
```bash
# Acceder a https://zentoerp.com/admin/
# Login con superusuario creado
```

## 📊 Costos Estimados

- **PostgreSQL Starter**: $7/mes
- **Redis Starter**: $7/mes  
- **Web Service Starter**: $7/mes
- **Total**: $21/mes

## 🔧 Troubleshooting

### **Build falla:**
- Verificar que `requirements.txt` esté actualizado
- Revisar logs de build en Render
- Confirmar que `scripts/render-deploy.sh` tenga permisos

### **No conecta a DB:**
- Verificar variables de entorno de base de datos
- Confirmar que PostgreSQL service esté running
- Revisar configuración de `DATABASES` en `production.py`

### **Subdominios no funcionan:**
- Verificar DNS wildcard (`CNAME * → zentoerp.com`)
- Confirmar `ALLOWED_HOSTS` incluye `*.zentoerp.com`
- Revisar configuración de tenant en Django

### **SSL no funciona:**
- Esperar hasta 1 hora para propagación
- Verificar que dominio esté agregado en Render
- Confirmar DNS apunte a Render

## 🎯 Próximos Pasos

Una vez completado el deploy:
- **Fase 5**: Testing y optimización
- **Fase 6**: Monitoreo y backup
- Crear primeros tenants
- Configurar email transaccional
- Implementar monitoreo avanzado

---

**¿Listo para comenzar con el deploy?** 🚀
