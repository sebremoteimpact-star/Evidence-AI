# ADR 0004 — Render en lugar de Railway

**Estado:** Aceptado · **Fecha:** 2026-06-26 · **Fase:** 2

## Contexto

Necesitamos hosting gratis para `api` y `worker` (Python en Docker). El spec original sugería Railway.

## Decisión

Desplegamos `api` y `worker` en **Render** free tier.

## Alternativas consideradas

- **Railway:** rechazado. Eliminaron el free tier permanente; ahora son créditos de prueba ($5 únicos).
- **Fly.io:** considerado. Free tier real pero más complejo (necesita CLI propia, configuración con `fly.toml`). Render gana por simplicidad.
- **Heroku free:** ya no existe.
- **Cloud Run (GCP):** free tier generoso pero requiere cuenta GCP con tarjeta, complejidad de IAM.
- **Self-host en VPS:** rechazado por gestión operativa (SSL, backups, monitoreo).

## Consecuencias

**Positivas:**
- Free tier permanente (con cold starts ~30s, aceptable para uso ligero).
- Despliegue Docker estándar, sin lock-in.
- Blueprint declarativo (`render.yaml`).

**Negativas:**
- Cold start del free tier: primer request tras inactividad tarda ~30s.
- Sin custom domain en free tier (requiere $7/mes plan).

## Cuándo revisar

Si recibimos tráfico real sostenido (>1000 req/día), pasamos al plan paid ($7/mes) o migramos a Fly.io.
