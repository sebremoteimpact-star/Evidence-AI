# Arquitectura — Evidence AI

> Documento vivo. Refleja decisiones acordadas hasta la Fase 3 del proyecto.
> Cambios significativos se registran como **ADRs** en [`DECISIONS/`](DECISIONS/).

---

## 1. Misión técnica

Evidence AI es una plataforma que recibe contenido (texto, URL, post, transcript, video) y produce un **reporte de evidencia auditable** con score de confianza calibrado. **Nunca afirma verdad o falsedad**: cuantifica el peso de la evidencia disponible.

---

## 2. Vista de contexto (C4 nivel 1)

```
                          ┌──────────────────────────────┐
                          │         Usuario              │
                          │ (Periodista, investigador,   │
                          │  educador, ciudadano)        │
                          └──────────────┬───────────────┘
                                         │ HTTPS
                                         ▼
                          ┌──────────────────────────────┐
                          │       Evidence AI            │
                          └──┬───┬───┬───┬───┬───┬───┬───┘
                             │   │   │   │   │   │   │
              ┌──────────────┘   │   │   │   │   │   └──────────────┐
              ▼                  ▼   ▼   ▼   ▼   ▼                  ▼
        ┌──────────┐      ┌──────────┐ ┌──────┐ ┌────────┐    ┌──────────┐
        │ Claude   │      │  DDG /   │ │PubMed│ │YouTube │    │  OAuth   │
        │   API    │      │ Brave /  │ │Cross-│ │transcr.│    │ (Google) │
        │          │      │ Google   │ │Ref...│ │  API   │    │          │
        └──────────┘      └──────────┘ └──────┘ └────────┘    └──────────┘
```

---

## 3. Vista de contenedores (C4 nivel 2)

| Contenedor | Tecnología | Responsabilidad | Despliegue |
|---|---|---|---|
| `web` | Next.js 14 + TypeScript | UI, SSR, dashboard, Auth.js | Vercel free |
| `api` | FastAPI + Pydantic v2 | REST + SSE para streaming de progreso | Render free |
| `worker` | arq (async Python) | Pipeline de verificación largo | Render free |
| `postgres` | PostgreSQL 16 + pgvector | Persistencia + similitud vectorial | Supabase free |
| `redis` | Redis 7 | Cache, rate limits, cola arq, pubsub para SSE | Upstash free |

---

## 4. Arquitectura interna del backend — Clean Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│   INTERFACES (FastAPI routers, schemas, worker entrypoint)          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ depende de ↓
┌──────────────────────────────▼──────────────────────────────────────┐
│   APPLICATION (Use cases + Ports/Protocols)                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ depende de ↓
┌──────────────────────────────▼──────────────────────────────────────┐
│   DOMAIN (Entidades, value objects, servicios — PURO)               │
└─────────────────────────────────────────────────────────────────────┘
                               ▲
                               │ implementa puertos
┌──────────────────────────────┴──────────────────────────────────────┐
│   INFRASTRUCTURE (Adaptadores: Claude, DDG, SQLAlchemy, Redis...)   │
└─────────────────────────────────────────────────────────────────────┘
```

**Reglas de import** (enforced por `import-linter` en CI):
- `domain` no importa de ninguna otra capa.
- `application` solo importa de `domain`.
- `infrastructure` implementa puertos de `application`; nadie en `domain` o `application` la importa.
- `interfaces` orquesta vía DI; no contiene lógica de negocio.

---

## 5. Pipeline de verificación

```
INPUT → INGESTOR → DETECTORES MANIPULACIÓN → EXTRACTOR DE CLAIMS
        ↓
        RECUPERACIÓN DE EVIDENCIA (por claim, paralelo)
          ├─ Generador de queries (Claude)
          ├─ Fan-out a proveedores (DDG, PubMed, CrossRef, ...)
          ├─ Fetcher con cache
          └─ Deduplicación + clustering
        ↓
        RANKING (tier + frescura + independencia + metodología)
        ↓
        RAZONADOR (Claude por claim, sobre evidencia recuperada)
        ↓
        CONFIANZA (fórmula determinista — NO Claude)
        ↓
        COMPOSITOR DEL REPORTE
        ↓
        REPORTE (DB + SSE al cliente)
```

Cada paso emite eventos vía Redis pubsub → SSE al frontend para mostrar progreso en vivo.

---

## 6. Aislamiento de prompt injection

Defensa en capas:

1. **Separación estructural** del prompt: contenido del usuario va en `<untrusted_content>` con instrucción explícita al modelo de tratarlo como dato.
2. **Salida forzada por schema** vía tool use de Claude.
3. **Validación Pydantic** post-hoc.
4. **Sanitización del input**: strip de caracteres de control, normalización Unicode, truncado.
5. **Sin acceso directo** de Claude a DB o secrets. El pipeline orquesta.

Ver [`PROMPTS.md`](PROMPTS.md) para detalle.

---

## 7. Estrategia de caching (Redis)

| Qué se cachea | TTL |
|---|---|
| Resultados de búsqueda `(query + proveedor)` | 24h |
| Contenido extraído de URLs | 7d |
| Transcripts de YouTube | 30d |
| Respuestas de Claude `(prompt_hash + content_hash)` | 7d |
| Rate limit counters | ventana 1h-24h |

---

## 8. Manejo de errores y degradación elegante

- Cada adaptador tiene **timeout estricto** y **circuit breaker** por proveedor.
- Resultado parcial es válido: si CrossRef cae, el reporte se genera con menos fuentes pero se anota la indisponibilidad.
- Solo Claude es crítico; si Claude cae, la verificación falla con error claro.

---

## 9. Seguridad transversal

| Vector | Mitigación |
|---|---|
| Prompt injection | Aislamiento estructural + salida por schema |
| SSRF en scraping | Allowlist de schemas, blocklist de IPs internas/metadata, check DNS rebinding |
| Abuso de scraping | robots.txt, User-Agent identificable, max 1 req/seg por dominio |
| SQL injection | SQLAlchemy 2.0 con params tipados, prohibido raw SQL |
| XSS en reportes compartidos | DOMPurify + CSP estricta |
| CSRF | Cookies SameSite=Lax + double-submit en mutaciones |
| Robo de API keys | Variables de entorno, rotación documentada |
| Upload malicioso | Validación magic bytes, tamaño máx, escaneo ClamAV (post-MVP) |
| DoS verificaciones costosas | Rate limit por usuario + per-IP + quota diaria de tokens Claude |

Ver [`SECURITY.md`](SECURITY.md).

---

## 10. Observabilidad

- **Logs:** structlog JSON
- **Trazas:** OpenTelemetry → Grafana Cloud free
- **Métricas:** Prometheus endpoint en api y worker
- **Errores:** Sentry free tier
- **Audit log:** registro inmutable de qué se consultó, qué se recibió y qué prompts se enviaron

---

## 11. Estructura del repositorio

Ver [`README.md`](../README.md) para el árbol completo.

---

## 12. Decisiones registradas

| ADR | Decisión |
|---|---|
| [0001](DECISIONS/0001-monorepo.md) | Monorepo en lugar de polyrepo |
| [0002](DECISIONS/0002-pgvector-vs-qdrant.md) | pgvector en lugar de Qdrant |
| [0003](DECISIONS/0003-arq-vs-celery.md) | arq en lugar de Celery |
| [0004](DECISIONS/0004-render-vs-railway.md) | Render en lugar de Railway |
| [0005](DECISIONS/0005-clean-architecture.md) | Clean Architecture estricta |
| [0006](DECISIONS/0006-sse-vs-websockets.md) | SSE en lugar de WebSockets |
