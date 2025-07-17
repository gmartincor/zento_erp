import os
from decouple import config, Csv
from .base import *

# SECURITY SETTINGS - Configuración robusta para larga duración
DEBUG = False

# Get allowed hosts from environment or use default
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

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
            'options': '-c default_transaction_isolation=read_committed -c statement_timeout=30000'
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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = config('STATIC_ROOT', default=os.path.join(BASE_DIR, 'static_collected'))
MEDIA_ROOT = config('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))

# Add whitenoise middleware
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

# Configuración de dominios permitidos para multi-tenant
ALLOWED_HOSTS = [
    TENANT_DOMAIN,
    f'*.{TENANT_DOMAIN}',
    '.zentoerp.com',
    'zentoerp.com',
]

# Agregar hosts adicionales desde variables de entorno
additional_hosts = config('ADDITIONAL_ALLOWED_HOSTS', default='', cast=Csv())
if additional_hosts:
    ALLOWED_HOSTS.extend(additional_hosts)

# Configuración de CORS para subdominios (si se usa)
CORS_ALLOWED_ORIGINS = [
    f"https://{TENANT_DOMAIN}",
    f"https://*.{TENANT_DOMAIN}",
]

# Configuración de cookies para subdominios
CSRF_COOKIE_DOMAIN = f'.{TENANT_DOMAIN}'
SESSION_COOKIE_DOMAIN = f'.{TENANT_DOMAIN}'
