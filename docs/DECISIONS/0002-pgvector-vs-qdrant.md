# ADR 0002 — pgvector en lugar de Qdrant

**Estado:** Aceptado · **Fecha:** 2026-06-26 · **Fase:** 2

## Contexto

El spec original pedía Qdrant como vector DB. Lo necesitamos para:
- Deduplicación de evidencia (¿este pasaje ya lo vimos en otra fuente?).
- Clustering de claims similares.
- Búsqueda semántica en evidencia previa.

## Decisión

Usamos **pgvector** (extensión de PostgreSQL) en lugar de Qdrant.

## Alternativas consideradas

- **Qdrant standalone (Docker o cloud):** rechazado para v1. Su free tier cloud es limitado y agrega un servicio más que mantener, contra el objetivo "completamente gratis y simple".
- **Pinecone / Weaviate:** rechazados — sin free tier sostenible.
- **In-memory (FAISS):** rechazado — perdemos persistencia.

## Consecuencias

**Positivas:**
- Un servicio menos que desplegar, monitorear y respaldar.
- Joins entre tablas relacionales y vectores en la misma query.
- Aprovechamos la misma DB que ya usamos para todo lo demás.

**Negativas:**
- Performance en colecciones >10M vectores empieza a degradarse (Qdrant escala mejor).
- Menos features avanzados (filtrado vectorial complejo, multi-tenancy nativo).

## Cuándo revisar

Si superamos 1M de pasajes indexados o p95 de búsqueda vectorial > 200ms, migramos a Qdrant. La interfaz `VectorStore` en `application/ports/` abstrae el storage, así que el swap es local.
