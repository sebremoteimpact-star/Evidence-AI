#!/usr/bin/env bash
# ─────────────────────────────────────────────
# Evidence AI — Bootstrap dev local (Unix)
# ─────────────────────────────────────────────
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Verificando prerrequisitos..."
missing=()
for tool in docker node pnpm uv; do
  command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Faltan herramientas: ${missing[*]}"
  echo "Instala: Docker, Node 20+, pnpm, uv (https://github.com/astral-sh/uv)"
  exit 1
fi

echo "==> Copiando .env.example -> .env si no existen..."
for envFile in ".env" "apps/api/.env" "apps/web/.env"; do
  dir=$(dirname "$envFile")
  if [ ! -f "$envFile" ] && [ -f "$dir/.env.example" ]; then
    cp "$dir/.env.example" "$envFile"
    echo "  creado: $envFile"
  fi
done

echo "==> Levantando Postgres + Redis..."
docker compose -f infra/docker/docker-compose.yml up -d postgres redis

echo "==> Esperando a que Postgres esté listo..."
for _ in {1..30}; do
  if docker compose -f infra/docker/docker-compose.yml exec -T postgres pg_isready -U evidence >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo
echo "Listo."
echo "  Postgres: localhost:5432 (db: evidence_ai, user: evidence)"
echo "  Redis:    localhost:6379"
echo
echo "Siguiente:"
echo "  1. Edita .env y agrega ANTHROPIC_API_KEY"
echo "  2. cd apps/api && uv sync"
echo "  3. cd apps/web && pnpm install"
echo "  4. make migrate"
echo "  5. make dev"
