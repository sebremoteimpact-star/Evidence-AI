-- ─────────────────────────────────────────────
-- Evidence AI — Extensiones de PostgreSQL
-- Se ejecuta automáticamente la primera vez que arranca el contenedor.
-- ─────────────────────────────────────────────

-- pgvector: similitud vectorial (para deduplicación de evidencia y clustering)
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm: búsqueda fuzzy por trigramas (útil para deduplicar fuentes)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- uuid-ossp: generación de UUIDs server-side
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- citext: tipos case-insensitive (emails, dominios)
CREATE EXTENSION IF NOT EXISTS citext;
