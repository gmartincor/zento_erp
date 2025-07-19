# =============================================================================
# DOCKERFILE MULTI-STAGE PARA ZENTOERP - DESARROLLO Y PRODUCCIÓN
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Node.js Builder - Compila TailwindCSS y assets frontend
# -----------------------------------------------------------------------------
FROM node:20.18.0-alpine AS frontend-builder

LABEL stage=frontend-builder
LABEL description="Compila TailwindCSS y assets frontend"

WORKDIR /frontend

# Actualizar el sistema y npm
RUN apk update && apk upgrade && \
    npm install -g npm@latest

# Copiar archivos de configuración Node.js
COPY package.json package-lock.json* ./

# Instalar dependencias Node.js (incluyendo devDependencies para el build)
RUN npm install

# Actualizar browserslist database (después de instalar dependencies)
RUN npx update-browserslist-db@latest

# Copiar archivos fuente necesarios para el build
COPY static/ ./static/
COPY templates/ ./templates/
COPY apps/ ./apps/
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Compilar TailwindCSS para producción
RUN npm run build-prod

# Verificar que el archivo CSS se compiló correctamente
RUN ls -la static/css/style.css && \
    echo "CSS compilado exitosamente: $(wc -c < static/css/style.css) bytes"

# -----------------------------------------------------------------------------
# STAGE 2: Python Base - Configuración base de Python
# -----------------------------------------------------------------------------
FROM python:3.12.7-slim AS python-base

LABEL stage=python-base
LABEL description="Configuración base de Python con dependencias del sistema"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema con actualizaciones de seguridad
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    # PostgreSQL client libraries
    libpq-dev \
    # Para compilar psycopg2
    gcc \
    # Para Pillow (procesamiento de imágenes)
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libffi-dev \
    # Herramientas de sistema
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip==24.0 setuptools wheel

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash --uid 1000 zentoerp

# Configurar permisos seguros
RUN chmod 755 /home/zentoerp

# -----------------------------------------------------------------------------
# STAGE 3: Dependencies - Instala dependencias Python
# -----------------------------------------------------------------------------
FROM python-base AS dependencies

LABEL stage=dependencies
LABEL description="Instala todas las dependencias Python"

WORKDIR /app

# Copiar requirements
COPY requirements.txt ./

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# -----------------------------------------------------------------------------
# STAGE 4: Development - Imagen para desarrollo
# -----------------------------------------------------------------------------
FROM dependencies AS development

LABEL stage=development
LABEL description="Imagen de desarrollo con herramientas adicionales"

# Instalar dependencias de desarrollo
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copiar código fuente
COPY --chown=zentoerp:zentoerp . .

# Copiar assets compilados desde frontend-builder
COPY --from=frontend-builder --chown=zentoerp:zentoerp /frontend/static/css/style.css ./static/css/style.css
COPY --from=frontend-builder --chown=zentoerp:zentoerp /frontend/static/js/ ./static/js/

# Cambiar a usuario no-root
USER zentoerp

# Exponer puerto para desarrollo
EXPOSE 8000

# Health check para desarrollo
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Comando por defecto para desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# -----------------------------------------------------------------------------
# STAGE 5: Production Builder - Prepara archivos para producción
# -----------------------------------------------------------------------------
FROM dependencies AS production-builder

LABEL stage=production-builder
LABEL description="Prepara la aplicación para producción"

WORKDIR /app

# Copiar código fuente
COPY . .

# Copiar assets compilados desde frontend-builder
COPY --from=frontend-builder /frontend/static/css/style.css ./static/css/style.css
COPY --from=frontend-builder /frontend/static/js/ ./static/js/

# Crear directorios necesarios
RUN mkdir -p static_collected media logs

# Configurar permisos
RUN chown -R zentoerp:zentoerp /app

# Cambiar a usuario no-root
USER zentoerp

# Compilar archivos estáticos (se ejecutará en runtime con variables de entorno)
# RUN python manage.py collectstatic --noinput

# -----------------------------------------------------------------------------
# STAGE 6: Production - Imagen final de producción
# -----------------------------------------------------------------------------
FROM python-base AS production

LABEL maintainer="ZentoERP <admin@zentoerp.com>"
LABEL version="1.0.0"
LABEL description="ZentoERP - Sistema ERP multi-tenant para nutricionistas"

WORKDIR /app

# Copiar dependencias instaladas
COPY --from=dependencies /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=dependencies /usr/local/bin/ /usr/local/bin/

# Copiar aplicación desde production-builder
COPY --from=production-builder --chown=zentoerp:zentoerp /app .

# Crear volúmenes para persistencia
VOLUME ["/app/media", "/app/logs"]

# Cambiar a usuario no-root
USER zentoerp

# Exponer puerto
EXPOSE 8000

# Health check para producción
HEALTHCHECK --interval=60s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Script de entrada
COPY --chown=zentoerp:zentoerp scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Comando por defecto para producción
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "sync", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "2", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "config.wsgi:application"]
