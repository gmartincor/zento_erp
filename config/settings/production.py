import os
from decouple import config, Csv
from .base import *

# SECURITY SETTINGS - Configuración robusta para larga duración
DEBUG = False

# ALLOWED_HOSTS - Configuración robusta para multi-tenant + Render
# Incluye dominios personalizados Y dominios de Render para health checks
ALLOWED_HOSTS = [
    # Dominio principal y subdominios
    TENANT_DOMAIN,                    # zentoerp.com
    f'*.{TENANT_DOMAIN}',            # *.zentoerp.com
    f'www.{TENANT_DOMAIN}',          # www.zentoerp.com
    '.zentoerp.com',                 # Cualquier subdominio
    'zentoerp.com',                  # Dominio raíz
    
    # Dominios de Render (CRÍTICOS para health checks)
    'zentoerp-web.onrender.com',     # Dominio específico de tu servicio
    '*.onrender.com',                # Cualquier subdominio de Render
    'localhost',                     # Para desarrollo local
    '127.0.0.1',                     # Para desarrollo local
]

# Agregar hosts adicionales desde variables de entorno (si existen)
additional_hosts = config('ADDITIONAL_ALLOWED_HOSTS', default='', cast=Csv())
if additional_hosts:
    ALLOWED_HOSTS.extend(additional_hosts)

# También leer de ALLOWED_HOSTS env var como fallback
env_allowed_hosts = config('ALLOWED_HOSTS', default='', cast=Csv())
if env_allowed_hosts:
    # Agregar hosts únicos de la variable de entorno
    for host in env_allowed_hosts:
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Security headers más robustos
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 63072000  # 2 años (más tiempo que el estándar)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'same-origin'  # Mejor seguridad

# Cookies más seguras
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'  # Protección adicional contra CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'  # Protección adicional

# Configuración XFrame más restrictiva
X_FRAME_OPTIONS = 'DENY'

# Configuración adicional para longevidad
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# DATABASE - Configuración optimizada para producción multi-tenant de larga duración
import dj_database_url

# Configuración primaria con DATABASE_URL (Render, Heroku, etc.)
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    # Usar DATABASE_URL si está disponible (Render, Heroku, etc.)
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=300)
    }
    # Configurar django-tenants engine
    DATABASES['default']['ENGINE'] = 'django_tenants.postgresql_backend'
    # Opciones optimizadas para producción
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
        'connect_timeout': 60,
    }
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
    DATABASES['default']['ATOMIC_REQUESTS'] = True
    DATABASES['default']['TIME_ZONE'] = 'UTC'
else:
    # Fallback a variables individuales
    DATABASES = {
        'default': {
            'ENGINE': 'django_tenants.postgresql_backend',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'sslmode': 'require',
                'connect_timeout': 60,
            },
            'CONN_MAX_AGE': 300,  # 5 minutos (más conservador para estabilidad)
            'CONN_HEALTH_CHECKS': True,
            'ATOMIC_REQUESTS': True,
            'TIME_ZONE': 'UTC',  # Especificar zona horaria
        }
    }

# EMAIL SETTINGS
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@miapp.com')

# CACHE - Configuración SIN Redis (modo económico)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
        'TIMEOUT': 300,  # 5 minutos
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Configuración de sesiones SIN Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 horas

# STATIC FILES SETTINGS
# =============================================================================
# Configuración robusta para archivos estáticos con Whitenoise para multi-tenant

# URL para archivos estáticos
STATIC_URL = '/static/'

# Directorios donde Django busca archivos estáticos antes de collectstatic
# CRÍTICO: Debe incluir el directorio donde se genera style.css
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Directorio donde está style.css
]

# Configuración de storage con Whitenoise optimizada para multi-tenant
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Directorio donde se recolectan los archivos estáticos
STATIC_ROOT = config('STATIC_ROOT', default=os.path.join(BASE_DIR, 'static_collected'))

# Finders de archivos estáticos (asegurar que están configurados)
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',  # Busca en STATICFILES_DIRS
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # Busca en apps
]

# Configuración especializada de Whitenoise para multi-tenant
WHITENOISE_USE_FINDERS = False  # Desactivar en producción para mejor rendimiento
WHITENOISE_AUTOREFRESH = False  # Desactivar en producción
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['js', 'css', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']
WHITENOISE_MAX_AGE = 31536000  # 1 año cache para archivos estáticos
WHITENOISE_INDEX_FILE = False  # Desactivar serving de index files
WHITENOISE_ROOT = STATIC_ROOT  # Asegurar que Whitenoise use el directorio correcto
WHITENOISE_MIMETYPES = {
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
}
# Configuración crítica para multi-tenant: permitir que Whitenoise sirva archivos 
# sin verificar el tenant en el host header
WHITENOISE_STATIC_PREFIX = '/static/'

# Media files
MEDIA_ROOT = config('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))
MEDIA_URL = '/media/'

# Configuración optimizada de Whitenoise para multi-tenant
# CRÍTICO: Whitenoise debe estar ANTES de SecurityMiddleware para funcionar con subdominios
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    # Buscar SecurityMiddleware e insertar Whitenoise ANTES
    try:
        security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
        MIDDLEWARE.insert(security_index, 'whitenoise.middleware.WhiteNoiseMiddleware')
    except ValueError:
        # Si no encuentra SecurityMiddleware, insertar después de TenantMainMiddleware
        try:
            tenant_index = MIDDLEWARE.index('django_tenants.middleware.main.TenantMainMiddleware')
            MIDDLEWARE.insert(tenant_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')
        except ValueError:
            # Último recurso: agregar al principio (después de debug middleware si existe)
            MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')



# Session configuration SIN Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 horas

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': config('LOG_FILE', default='/tmp/django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django_tenants': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Secret key - must be set in environment
SECRET_KEY = config('SECRET_KEY')

# MULTI-TENANT DOMAIN CONFIGURATION
# =============================================================================
# Configuración específica para zentoerp.com con subdominios

# Dominio principal para la aplicación
TENANT_DOMAIN = config('TENANT_DOMAIN', default='zentoerp.com')

# Configuración específica para django-tenants
TENANT_MODEL = 'tenants.Tenant'
TENANT_DOMAIN_MODEL = 'tenants.Domain'

# Configuración de subdominios
TENANT_SUBFOLDER_PREFIX = ''  # Solo subdominios, no subcarpetas
TENANT_LIMIT_SET_CALLS = True  # Optimización para producción

# ALLOWED_HOSTS ya está configurado arriba - no redefinir aquí

# Configuración de CORS para subdominios (si se usa)
CORS_ALLOWED_ORIGINS = [
    f"https://{TENANT_DOMAIN}",
    f"https://*.{TENANT_DOMAIN}",
    "https://zentoerp.com",
    "https://*.zentoerp.com",
]

# Configuración adicional para archivos estáticos cross-origin
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_PREFLIGHT_MAX_AGE = 86400

# Configuración de cookies para subdominios
CSRF_COOKIE_DOMAIN = f'.{TENANT_DOMAIN}'
SESSION_COOKIE_DOMAIN = f'.{TENANT_DOMAIN}'
