"""FastAPI app factory.

Punto de entrada del API. Uvicorn lo invoca como:
    uvicorn evidence_ai.interfaces.http.app:create_app --factory
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from evidence_ai.config.container import Container
from evidence_ai.config.settings import get_settings
from evidence_ai.infrastructure.observability.logging import configure_logging, get_logger
from evidence_ai.infrastructure.persistence.models import UserModel
from evidence_ai.interfaces.http.dependencies import GUEST_USER_EMAIL, GUEST_USER_ID
from evidence_ai.interfaces.http.middleware.error_handler import register_error_handlers
from evidence_ai.interfaces.http.middleware.request_id import RequestIdMiddleware
from evidence_ai.interfaces.http.routers import auth, health, stream, verifications

logger = get_logger(__name__)


async def _ensure_guest_user(session_factory) -> None:
    """Crea el usuario invitado si no existe. Idempotente."""
    async with session_factory() as session:
        existing = await session.execute(
            select(UserModel).where(UserModel.id == GUEST_USER_ID)
        )
        if existing.scalar_one_or_none() is not None:
            return
        session.add(UserModel(
            id=GUEST_USER_ID,
            email=GUEST_USER_EMAIL,
            name="Invitado",
            password_hash=None,
            oauth_provider=None,
            oauth_subject=None,
            locale="es",
            is_active=True,
            is_admin=False,
        ))
        try:
            await session.commit()
            logger.info("guest_user_created", user_id=str(GUEST_USER_ID))
        except Exception as e:
            await session.rollback()
            # Otra instancia lo creó al mismo tiempo — OK
            logger.info("guest_user_create_skipped", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa recursos al arrancar y los libera al apagar."""
    container: Container = app.state.container
    await container.init_resources()
    await _ensure_guest_user(container.session_factory())
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
    # CORS abierto a todos los orígenes (modo invitado, sin cookies).
    # JWT va en header Authorization, no en cookies, así que allow_credentials=False
    # permite usar wildcard "*" sin problemas de seguridad de navegador.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestIdMiddleware)

    # ── Manejadores de error (RFC 7807) ──
    register_error_handlers(app)

    # ── Routers ──
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(verifications.router)
    app.include_router(stream.router)

    return app
