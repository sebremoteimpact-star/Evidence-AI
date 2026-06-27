# Evidence AI

> Plataforma de verificación de evidencia asistida por IA.
> **No decide qué es verdadero**. Recolecta evidencia de fuentes independientes, compara, calcula confianza y explica por qué.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Estado](https://img.shields.io/badge/estado-en%20construcci%C3%B3n-orange.svg)]()

---

## ¿Qué hace?

Pegas un texto, una URL, un post de redes sociales, un transcript o el enlace de un video. El sistema:

1. **Extrae los claims** (afirmaciones factuales) del contenido.
2. **Separa hechos de opiniones**, detecta lenguaje emocional, clickbait, propaganda, estadísticas manipuladas, contexto faltante y marcadores de generación por IA.
3. **Busca evidencia** en múltiples fuentes independientes, priorizando: papers peer-reviewed → documentos oficiales → organizaciones internacionales → fact-checkers → academia → periodismo profesional.
4. **Compara la evidencia**, identifica contradicciones, calcula un **score de confianza** auditable.
5. **Genera un reporte ejecutivo** en tu idioma con citas exactas a cada fuente.

**Nunca dice "esto es verdadero" o "esto es falso".** Dice "la evidencia disponible apoya / contradice / es insuficiente para sostener esta afirmación".

---

## Stack

**Frontend:** Next.js 14 · TypeScript · TailwindCSS · shadcn/ui · Framer Motion · Auth.js
**Backend:** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · arq (worker)
**Datos:** PostgreSQL 16 + pgvector · Redis 7
**IA:** Claude API (`claude-sonnet-4-6` razonamiento, `claude-haiku-4-5-20251001` tareas rápidas)
**Búsqueda:** DuckDuckGo (default) + adaptadores Brave / Google CSE · PubMed · CrossRef · Semantic Scholar · OpenAlex · arXiv · WHO · World Bank · Our World in Data · IFCN fact-checkers
**Despliegue:** Vercel (web) + Render (api, worker) + Supabase (Postgres) + Upstash (Redis) — todo en free tier
**Dev local:** Docker Compose

---

## Inicio rápido

> Requiere: Docker Desktop, Node 20+, Python 3.12+, [uv](https://github.com/astral-sh/uv), [pnpm](https://pnpm.io/).

```bash
# 1. Clonar
git clone <url> evidence-ai && cd evidence-ai

# 2. Configurar variables de entorno
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# Edita .env y agrega tu ANTHROPIC_API_KEY

# 3. Levantar servicios de datos (postgres + redis)
make dev-db

# 4. Aplicar migraciones
make migrate

# 5. Levantar todo
make dev
```

Frontend: http://localhost:3000
API: http://localhost:8000
Docs API (OpenAPI): http://localhost:8000/docs

---

## Estructura del repositorio

```
evidence-ai/
├── apps/
│   ├── web/        # Next.js frontend
│   └── api/        # FastAPI backend + arq worker
├── packages/
│   ├── shared-types/    # Tipos TS auto-generados desde OpenAPI
│   └── source-registry/ # Mapeo dominio → tier de fuente
├── infra/
│   ├── docker/     # docker-compose para dev local
│   ├── render/     # blueprint despliegue Render
│   └── vercel/     # config Vercel
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS/  # Architecture Decision Records (ADRs)
│   ├── API.md
│   ├── PROMPTS.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   └── USAGE.md
└── scripts/
```

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para el detalle completo de la arquitectura.

---

## Filosofía del proyecto

- **La evidencia es primaria, la opinión es secundaria.** Las fuentes se rankean en 6 niveles según transparencia metodológica e independencia.
- **El modelo nunca afirma verdad.** Solo describe el peso de la evidencia recolectada.
- **Cada afirmación del reporte cita su fuente** con timestamp de recuperación.
- **El razonamiento es auditable.** El score de confianza se desglosa por factor; los prompts a Claude están versionados en `apps/api/src/evidence_ai/infrastructure/ai/prompts/`.
- **Open source, gratis, sin lock-in.** MIT, sin tracking, ejecutable enteramente en infraestructura gratuita.

---

## Contribuir

Ver [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) (próximamente).

## Licencia

[MIT](LICENSE)
