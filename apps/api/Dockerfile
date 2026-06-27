# ─────────────────────────────────────────────
# Evidence AI — API (FastAPI)
# Multi-stage para imagen pequeña en producción
# ─────────────────────────────────────────────
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# ─────────────────────────────────────────────
# Stage: deps (cacheable)
# ─────────────────────────────────────────────
FROM base AS deps
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev 2>/dev/null || uv sync --no-install-project --no-dev

# ─────────────────────────────────────────────
# Stage: runtime
# ─────────────────────────────────────────────
FROM base AS runtime
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .
RUN uv sync --no-dev 2>/dev/null || true

# Usuario no-root
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

# Migraciones + uvicorn. exec form ["sh","-c",...] evita problemas de parsing
# en plataformas como Render que pasan el CMD sin shell wrapping.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn evidence_ai.interfaces.http.app:create_app --factory --host 0.0.0.0 --port 8000"]
