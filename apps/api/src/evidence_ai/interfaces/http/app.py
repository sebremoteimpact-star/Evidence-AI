"""FastAPI app factory.

Punto de entrada del API. Uvicorn lo invoca como:
    uvicorn evidence_ai.interfaces.http.app:create_app --factory
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from evidence_ai.config.container import Container
from evidence_ai.config.settings import get_settings
from evidence_ai.infrastructure.observability.logging import configure_logging, get_logger
from evidence_ai.interfaces.http.middleware.error_handler import register_error_handlers
from evidence_ai.interfaces.http.middleware.request_id import RequestIdMiddleware
from evidence_ai.interfaces.http.routers import auth, health, stream, verifications

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa recursos al arrancar y los libera al apagar."""
    container: Container = app.state.container
    # Inicializar resources (Redis, arq pool)
    await container.init_resources()
    logger.info("api_started", environment=container.settings().environment)
    try:
        yield
    finally:
        await container.shutdown_resources()
        logger.info("api_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    # Logging primero (para que el resto loguee con formato correcto)
    configure_logging(
        level=settings.log_level,
        json_logs=settings.is_production,
    )

    # DI container
    container = Container()
    container.wire()

    app = FastAPI(
        title="Evidence AI",
        description=(
            "Plataforma de verificación de evidencia asistida por IA. "
            "No decide qué es verdadero — recolecta evidencia, compara fuentes, "
            "calcula confianza y explica por qué."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.container = container

    # ── Middleware ──
    cors_kwargs: dict = {
        "allow_origins": settings.cors_origins_list,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["*"],
        "expose_headers": ["X-Request-ID"],
    }
    if settings.cors_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex
    app.add_middleware(CORSMiddleware, **cors_kwargs)
    app.add_middleware(RequestIdMiddleware)

    # ── Manejadores de error (RFC 7807) ──
    register_error_handlers(app)

    # ── Routers ──
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(verifications.router)
    app.include_router(stream.router)

    return app
