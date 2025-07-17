# =============================================================================
# Makefile - ZentoERP Commands (Fases 1-4)
# =============================================================================

.PHONY: help dev full-dev prod build clean test logs deploy verify-prod create-tenant

# Variables
COMPOSE_FILE := docker-compose.yml
PROJECT_NAME := zentoerp

# =============================================================================
# HELP
# =============================================================================
help: ## Mostrar ayuda
	@echo "🐳 ZentoERP - Comandos disponibles:"
	@echo ""
	@echo "DESARROLLO:"
	@echo "  dev          - Desarrollo básico (PostgreSQL + App)"
	@echo "  full-dev     - Desarrollo completo (PostgreSQL + Redis + App)"
	@echo "  build        - Rebuild imágenes"
	@echo "  clean        - Limpiar containers y volúmenes"
	@echo "  test         - Ejecutar tests"
	@echo "  logs         - Ver logs"
	@echo ""
	@echo "PRODUCCIÓN:"
	@echo "  verify-prod  - Verificar configuración de producción"
	@echo "  deploy       - Deploy a Render"
	@echo "  create-tenant - Crear nuevo tenant"
	@echo ""
	@echo "  clean        - Limpiar contenedores"
	@echo "  test         - Ejecutar tests"
	@echo "  logs         - Ver logs"
	@echo "  setup        - Configurar entorno inicial"
	@echo ""

# =============================================================================
# DEVELOPMENT
# =============================================================================
dev: ## Desarrollo básico
	@echo "🚀 Iniciando desarrollo básico..."
	@docker-compose --profile dev up --remove-orphans

full-dev: ## Desarrollo completo
	@echo "🚀 Iniciando desarrollo completo..."
	@docker-compose --profile full-dev up --remove-orphans

# =============================================================================
# PRODUCTION
# =============================================================================
prod: ## Producción
	@echo "🏭 Iniciando producción..."
	@docker-compose --profile prod up --remove-orphans

# =============================================================================
# BUILD & MAINTENANCE
# =============================================================================
build: ## Rebuild imágenes
	@echo "🔨 Rebuilding imágenes..."
	@docker-compose build --no-cache

clean: ## Limpiar contenedores
	@echo "🧹 Limpiando contenedores..."
	@docker-compose down -v --remove-orphans

# =============================================================================
# TESTING
# =============================================================================
test: ## Ejecutar tests
	@echo "🧪 Ejecutando tests..."
	@docker-compose --profile dev run --rm app-dev python manage.py test

# =============================================================================
# UTILS
# =============================================================================
logs: ## Ver logs
	@docker-compose logs -f app-dev

setup: ## Configurar entorno inicial
	@echo "⚙️ Configurando entorno inicial..."
	@./scripts/setup.sh

# =============================================================================
# SHORTCUTS
# =============================================================================
up: dev ## Alias para 'dev'
down: ## Parar servicios
	@docker-compose down

# =============================================================================
# PRODUCTION COMMANDS
# =============================================================================

verify-prod: ## Verificar configuración de producción
	@echo "🔍 Verificando configuración de producción..."
	python manage.py check_production_ready

deploy: ## Preparar para deploy en Render
	@echo "🚀 Preparando deploy para Render..."
	@echo "1. Verificando configuración..."
	python manage.py check_production_ready
	@echo "2. Ejecutando tests..."
	python manage.py test --keepdb --parallel
	@echo "3. Listo para deploy en Render"
	@echo "   - Hacer push a branch 'production'"
	@echo "   - Configurar variables de entorno en Render"
	@echo "   - Activar deploy automático"

create-tenant: ## Crear nuevo tenant
	@echo "🏢 Crear nuevo tenant:"
	@echo "Uso: make create-tenant SCHEMA=nutricion DOMAIN=nutricion.zentoerp.com NAME='Nutrición Pro'"
	@if [ -z "$(SCHEMA)" ] || [ -z "$(DOMAIN)" ] || [ -z "$(NAME)" ]; then \
		echo "❌ Error: Especificar SCHEMA, DOMAIN y NAME"; \
		echo "Ejemplo: make create-tenant SCHEMA=nutricion DOMAIN=nutricion.zentoerp.com NAME='Nutrición Pro'"; \
		exit 1; \
	fi
	python manage.py create_tenant $(SCHEMA) $(DOMAIN) "$(NAME)"

# Default target
.DEFAULT_GOAL := help
