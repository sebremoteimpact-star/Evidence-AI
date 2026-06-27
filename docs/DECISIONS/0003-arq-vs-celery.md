# ADR 0003 — arq en lugar de Celery

**Estado:** Aceptado · **Fecha:** 2026-06-26 · **Fase:** 2

## Contexto

El pipeline de verificación puede tardar 60-180s (claims × búsquedas paralelas × razonamiento Claude). Necesitamos una cola de jobs para no bloquear el event loop del API.

## Decisión

Usamos **arq** (Redis-based, async-native).

## Alternativas consideradas

- **Celery:** rechazado. Maduro y ubicuo, pero síncrono por defecto, configuración compleja, peso considerable. Mezcla sync/async es problemática con nuestro stack 100% async (FastAPI + asyncpg + httpx).
- **RQ:** rechazado por las mismas razones que Celery (sync).
- **Dramatiq:** considerado; arq se eligió por integración más fluida con asyncio y broker único (Redis, ya en el stack).
- **FastAPI BackgroundTasks:** rechazado — corre en el mismo proceso del API, no escala horizontalmente, no persiste.

## Consecuencias

**Positivas:**
- Sintaxis natural async para tareas que llaman Claude y APIs externas en paralelo.
- Mismo Redis para cola + cache + pubsub.
- ~1000 LOC en arq vs ~50k en Celery → fácil de debuggear.

**Negativas:**
- Menos ecosistema (no hay Flower equivalente para dashboards).
- Menos battle-tested en cargas extremas.

## Cuándo revisar

Si necesitamos rate limiting por worker, retries con backoff exponencial complejos, o priority queues, evaluamos Celery o Temporal.
