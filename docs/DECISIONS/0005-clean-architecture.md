# ADR 0005 — Clean Architecture estricta en el backend

**Estado:** Aceptado · **Fecha:** 2026-06-26 · **Fase:** 3

## Contexto

El pipeline de verificación cruza muchas fronteras (DB, Claude, scraping, búsqueda, eventos, cache). Sin disciplina arquitectónica, en 3 meses tenemos spaghetti intestable.

## Decisión

Backend organizado en 4 capas con dependencias estrictas (Domain → Application → Infrastructure → Interfaces):

```
interfaces      → orquesta vía DI, no contiene lógica
infrastructure  → implementa puertos definidos en application
application     → casos de uso + puertos (interfaces abstractas)
domain          → entidades + value objects + servicios puros
```

**Reglas enforced por `import-linter` en CI:**
- `domain` no importa de nadie (solo stdlib + pydantic.dataclasses).
- `application` solo importa de `domain`.
- `domain` y `application` no pueden importar FastAPI, SQLAlchemy, anthropic, httpx, redis, alembic.

## Alternativas consideradas

- **Estructura plana tipo "routers + services + models":** rechazado. Funciona en MVP pero se rompe cuando crecen las integraciones.
- **Hexagonal pura (sin distinción domain/application):** considerado; mantenemos la distinción porque el cálculo de confidence_score es lógica de dominio pura, no orquestación.

## Consecuencias

**Positivas:**
- El pipeline completo se testea con mocks de los puertos. Sin DB, sin red.
- Cambiar proveedor de búsqueda o de IA = nuevo adaptador, cero cambios en casos de uso.
- El código del dominio sobrevive a refactors de framework.

**Negativas:**
- Más boilerplate inicial (puertos + mappers + DTOs).
- Curva de aprendizaje para devs nuevos.

## Cumplimiento

CI ejecuta `lint-imports` que falla si alguien viola las reglas. No hay excepciones.
