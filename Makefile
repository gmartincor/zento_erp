# =============================================================================
# Makefile - ZentoERP SIMPLE Commands
# =============================================================================

.PHONY: help dev full-dev prod build clean test logs

# Variables
COMPOSE_FILE := docker-compose.yml
PROJECT_NAME := zentoerp

# =============================================================================
# HELP
# =============================================================================
help: ## Mostrar ayuda
	@echo "🐳 ZentoERP - Comandos disponibles:"
	@echo ""
	@echo "  dev          - Desarrollo básico (PostgreSQL + App)"
	@echo "  full-dev     - Desarrollo completo (PostgreSQL + Redis + App)"
	@echo "  prod         - Producción"
	@echo "  build        - Rebuild imágenes"
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

# Default target
.DEFAULT_GOAL := help
