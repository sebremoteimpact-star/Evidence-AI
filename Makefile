# ─────────────────────────────────────────────
# Evidence AI — Makefile
# ─────────────────────────────────────────────
# Comandos comunes para desarrollo y CI.
# Cross-platform: detecta Windows vs Unix.

SHELL := /bin/bash
DC := docker compose -f infra/docker/docker-compose.yml

.DEFAULT_GOAL := help

# ─────────────────────────────────────────────
.PHONY: help
help: ## Muestra este mensaje
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─────────────────────────────────────────────
# Dev local
# ─────────────────────────────────────────────
.PHONY: dev
dev: ## Levanta todo el stack (postgres + redis + api + worker + web)
	$(DC) up -d

.PHONY: dev-db
dev-db: ## Levanta solo Postgres + Redis
	$(DC) up -d postgres redis

.PHONY: down
down: ## Detiene todos los contenedores
	$(DC) down

.PHONY: clean
clean: ## Detiene y borra volúmenes (CUIDADO: borra la DB local)
	$(DC) down -v

.PHONY: logs
logs: ## Sigue los logs de todos los servicios
	$(DC) logs -f

# ─────────────────────────────────────────────
# Migraciones (Alembic)
# ─────────────────────────────────────────────
.PHONY: migrate
migrate: ## Aplica migraciones pendientes
	cd apps/api && uv run alembic upgrade head

.PHONY: migration
migration: ## Crea una nueva migración (uso: make migration MSG="descripcion")
	cd apps/api && uv run alembic revision --autogenerate -m "$(MSG)"

.PHONY: migrate-down
migrate-down: ## Revierte la última migración
	cd apps/api && uv run alembic downgrade -1

# ─────────────────────────────────────────────
# Tipos compartidos
# ─────────────────────────────────────────────
.PHONY: types
types: ## Regenera tipos TypeScript desde el OpenAPI del backend
	bash scripts/generate-types.sh

# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────
.PHONY: test
test: test-api test-web ## Ejecuta toda la suite

.PHONY: test-api
test-api: ## Tests del backend
	cd apps/api && uv run pytest

.PHONY: test-web
test-web: ## Tests del frontend
	cd apps/web && pnpm test

.PHONY: test-e2e
test-e2e: ## Tests end-to-end (Playwright)
	cd apps/web && pnpm test:e2e

# ─────────────────────────────────────────────
# Lint / format
# ─────────────────────────────────────────────
.PHONY: lint
lint: lint-api lint-web ## Lint en todo el repo

.PHONY: lint-api
lint-api:
	cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy src/

.PHONY: lint-web
lint-web:
	cd apps/web && pnpm lint && pnpm typecheck

.PHONY: format
format: ## Formatea automáticamente
	cd apps/api && uv run ruff format . && uv run ruff check --fix .
	cd apps/web && pnpm format

# ─────────────────────────────────────────────
# Instalación inicial
# ─────────────────────────────────────────────
.PHONY: install
install: install-api install-web ## Instala dependencias de api y web

.PHONY: install-api
install-api:
	cd apps/api && uv sync

.PHONY: install-web
install-web:
	cd apps/web && pnpm install

# ─────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────
.PHONY: shell-api
shell-api: ## Abre una shell en el contenedor del API
	$(DC) exec api bash

.PHONY: shell-db
shell-db: ## Abre psql en la DB local
	$(DC) exec postgres psql -U evidence -d evidence_ai
