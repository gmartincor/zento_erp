# 🌐 FASE 3: Configuración DNS y Dominio - zentoerp.com

## 📋 Resumen de la Fase 3

Esta fase configura el dominio `zentoerp.com` para funcionar con subdominios multi-tenant en Render, aplicando las mejores prácticas de infraestructura y seguridad.

## 🎯 Objetivos Completados

### ✅ 1. Configuración de Render
- **Archivo**: `render.yaml`
- **Propósito**: Infraestructura como código (IaC) para Render
- **Incluye**: Web service, PostgreSQL, Redis, dominios, SSL

### ✅ 2. Configuración DNS
- **Archivo**: `scripts/dns-config.sh`
- **Propósito**: Guía completa de configuración DNS
- **Incluye**: Records A, CNAME, MX, SSL wildcard

### ✅ 3. Optimización de Producción
- **Archivo**: `config/settings/production.py` (mejorado)
- **Mejoras**: Base de datos, cache, multi-tenant, seguridad
- **Rendimiento**: Conexiones persistentes, cache Redis optimizado

### ✅ 4. Variables de Entorno
- **Archivo**: `.env.production.template`
- **Propósito**: Template para configuración en Render
- **Seguridad**: Sin valores reales, solo estructura

### ✅ 5. Validación DNS
- **Archivo**: `scripts/validate-dns.sh`
- **Propósito**: Validar configuración antes del deploy
- **Incluye**: Tests de DNS, SSL, HTTP, subdominios

## 🚀 Configuración DNS Requerida

### 📍 Dominio Principal
```
Tipo: A
Nombre: @
Valor: [IP automática de Render]
TTL: 300
```

### 🔄 Subdominio WWW
```
Tipo: CNAME
Nombre: www
Valor: zentoerp.com
TTL: 300
```

### 🏢 Subdominios Multi-tenant
```
Tipo: CNAME
Nombre: *
Valor: zentoerp.com
TTL: 300
```

### 📧 Email (Opcional)
```
Tipo: MX
Nombre: @
Valor: [servidor de email]
Prioridad: 10
TTL: 3600
```

## 🔧 Configuración en Render

### 1. Crear Servicios
```bash
# Usar el archivo render.yaml para crear:
# - Web Service (Django)
# - PostgreSQL Database
# - Redis Cache
```

### 2. Configurar Dominio
```
Dashboard → Custom Domains → Add Domain
- zentoerp.com
- *.zentoerp.com (wildcard)
```

### 3. Variables de Entorno
```bash
# Usar .env.production.template como guía
# Configurar en Render Dashboard → Environment
```

## 🛠️ Comandos Útiles

### Validar DNS
```bash
chmod +x scripts/validate-dns.sh
./scripts/validate-dns.sh
```

### Información DNS
```bash
chmod +x scripts/dns-config.sh
./scripts/dns-config.sh
```

### Verificar Configuración
```bash
# DNS
dig zentoerp.com
dig www.zentoerp.com
dig nutricion.zentoerp.com

# SSL
openssl s_client -connect zentoerp.com:443

# HTTP
curl -I https://zentoerp.com
curl -I https://nutricion.zentoerp.com
```

## 📊 Mejoras de Rendimiento

### Base de Datos
- **Conexiones persistentes**: CONN_MAX_AGE=600
- **Health checks**: CONN_HEALTH_CHECKS=True
- **Transacciones atómicas**: ATOMIC_REQUESTS=True
- **Timeout optimizado**: connect_timeout=60

### Cache Redis
- **Pool de conexiones**: max_connections=50
- **Compresión**: ZlibCompressor
- **Timeout**: 300 segundos
- **Tolerancia a fallos**: IGNORE_EXCEPTIONS=True

### Configuración Multi-tenant
- **Optimización**: TENANT_LIMIT_SET_CALLS=True
- **Dominio base**: zentoerp.com
- **Subdominios**: *.zentoerp.com
- **Cookies compartidas**: .zentoerp.com

## 🔒 Seguridad Implementada

### SSL/TLS
- **HTTPS forzado**: SECURE_SSL_REDIRECT=True
- **HSTS**: 1 año con subdominios
- **Certificados**: Let's Encrypt automático
- **Wildcard SSL**: Para todos los subdominios

### Headers de Seguridad
- **X-Frame-Options**: DENY
- **Content-Type**: nosniff
- **XSS Protection**: Activado
- **CSRF Protection**: Configurado para subdominios

### Cookies Seguras
- **HttpOnly**: Activado
- **Secure**: Solo HTTPS
- **SameSite**: Configurado
- **Domain**: .zentoerp.com

## 📝 Checklist de Configuración

### DNS
- [ ] Dominio principal (A record)
- [ ] Wildcard subdomain (CNAME *)
- [ ] WWW subdomain (CNAME www)
- [ ] MX records (si se usa email)

### Render
- [ ] Servicios creados (Web, DB, Redis)
- [ ] Variables de entorno configuradas
- [ ] Dominios personalizados agregados
- [ ] SSL activado y verificado

### Validación
- [ ] DNS propagado correctamente
- [ ] SSL funcionando en dominio principal
- [ ] SSL funcionando en subdominios
- [ ] Health check respondiendo
- [ ] Aplicación accesible vía HTTPS

## 🔍 Troubleshooting

### DNS no propaga
- **Tiempo**: 24-48 horas máximo
- **Verificar**: https://whatsmydns.net/
- **TTL**: Usar valores bajos (300s) inicialmente

### SSL no funciona
- **Verificar**: Dominio agregado en Render
- **Wildcard**: Asegurar *.zentoerp.com configurado
- **Tiempo**: Puede tardar hasta 1 hora

### Subdominios no funcionan
- **CNAME**: Verificar record * apunta a zentoerp.com
- **Django**: Verificar ALLOWED_HOSTS incluye *.zentoerp.com
- **Cache**: Limpiar cache DNS local

## 🎯 Próximos Pasos

La **Fase 3** está completa. Siguiente etapa:

**FASE 4: Configuración de Render y Deploy**
- Configurar servicios en Render
- Deploy inicial
- Configurar base de datos
- Configurar Redis
- Pruebas de conectividad

## 📚 Recursos Adicionales

- [Render Custom Domains](https://render.com/docs/custom-domains)
- [Django-tenants Documentation](https://django-tenants.readthedocs.io/)
- [DNS Propagation Checker](https://whatsmydns.net/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)

---

**✅ Fase 3 completada con éxito**
**🎯 Ready para Fase 4: Configuración de Render y Deploy**
