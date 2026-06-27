"""Health checks."""

from __future__ import annotations

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from evidence_ai.config.container import Container

router = APIRouter(tags=["sistema"])


class HealthResponse(BaseModel):
    status: str
    service: str = "evidence-ai-api"
    version: str = "0.1.0"


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get("/health", response_model=HealthResponse, summary="Liveness")
async def health() -> HealthResponse:
    """Simple liveness probe — el proceso está corriendo."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness")
@inject
async def ready(
    session_factory: Annotated[
        async_sessionmaker[AsyncSession],
        Depends(Provide[Container.session_factory]),
    ],
    redis: Annotated[Redis, Depends(Provide[Container.redis])],
) -> ReadinessResponse:
    """Readiness probe — DB y Redis responden."""
    checks: dict[str, str] = {}
    overall = "ok"

    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"
        overall = "degraded"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        overall = "degraded"

    return ReadinessResponse(status=overall, checks=checks)
