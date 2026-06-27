#!/usr/bin/env bash
# ─────────────────────────────────────────────
# Regenera tipos TypeScript desde el OpenAPI del backend
# Requiere que el API esté corriendo en localhost:8000
# ─────────────────────────────────────────────
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Verificar que el API responde
if ! curl -sf http://localhost:8000/openapi.json -o /dev/null; then
  echo "Error: el API no responde en http://localhost:8000"
  echo "Levantalo con: make dev"
  exit 1
fi

cd "$ROOT/packages/shared-types"
pnpm exec openapi-typescript http://localhost:8000/openapi.json -o ./src/api.generated.ts

# Copia al frontend para imports cortos
cp ./src/api.generated.ts "$ROOT/apps/web/src/types/api.generated.ts"

echo "Tipos regenerados:"
echo "  packages/shared-types/src/api.generated.ts"
echo "  apps/web/src/types/api.generated.ts"
