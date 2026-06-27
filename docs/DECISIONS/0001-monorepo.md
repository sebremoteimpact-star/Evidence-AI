# ADR 0001 — Monorepo en lugar de polyrepo

**Estado:** Aceptado · **Fecha:** 2026-06-26 · **Fase:** 3

## Contexto

Evidence AI tiene dos aplicaciones desplegables (`web` en Next.js y `api`/`worker` en Python) más paquetes compartidos (tipos generados, registry de fuentes). Necesitamos decidir cómo organizar el código fuente.

## Decisión

Usamos **monorepo** con la estructura:
```
evidence-ai/
├── apps/        # cosas desplegables
├── packages/    # código compartido
├── infra/, docs/, scripts/
```

## Alternativas consideradas

- **Polyrepo (3+ repos separados):** rechazado. Cambios atómicos cross-stack (un cambio de schema en el backend que toca el frontend) requerirían PRs coordinados en repos separados, con tags/versiones.
- **Monorepo con pnpm workspaces + Turborepo:** rechazado por overkill para 2 apps. Si crecemos a >5 paquetes lo introducimos.

## Consecuencias

**Positivas:**
- Un PR puede modificar backend + frontend + docs atómicamente.
- Tipos generados desde OpenAPI viajan sin overhead de publicación.
- CI más simple: un único checkout cubre todo.

**Negativas:**
- El repo crece más rápido; herramientas como `git clone --depth` se vuelven necesarias.
- Acoplamiento implícito si no respetamos los límites de `apps/`.

## Cumplimiento

- CI separa jobs por carpeta (`paths` filters) para no rebuildear todo en cada PR.
- Reglas de import dentro de `apps/api` enforced por `import-linter`.
