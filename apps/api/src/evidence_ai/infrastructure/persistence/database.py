"""Engine y session factory de SQLAlchemy async.

Una sola instancia del engine por proceso (settings → engine → session factory).
La inyección al resto del código pasa por el container DI (Fase 5+).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from evidence_ai.config.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Crea el engine async. echo=False en producción para no loggear queries."""
    return create_async_engine(
        settings.database_url,
        echo=settings.environment == "development" and settings.log_level == "DEBUG",
        pool_pre_ping=True,  # ping antes de cada uso (evita conexiones muertas)
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,  # recicla conexiones cada 30 min
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # acceder a atributos tras commit sin re-query
        autoflush=False,
    )


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Context manager: abre sesión, hace commit al salir, rollback si excepción."""
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
