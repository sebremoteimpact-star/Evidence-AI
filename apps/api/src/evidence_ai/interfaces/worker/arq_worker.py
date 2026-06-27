"""Entry point del worker arq.

Arrancar con: arq evidence_ai.interfaces.worker.arq_worker.WorkerSettings
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from arq.connections import RedisSettings

from evidence_ai.config.container import Container
from evidence_ai.config.settings import get_settings
from evidence_ai.domain.services.confidence_calculator import ConfidenceCalculator
from evidence_ai.infrastructure.ai.claude_reasoner import ClaudeAIReasoner
from evidence_ai.infrastructure.fetchers.readability_fetcher import ReadabilityFetcher
from evidence_ai.infrastructure.fetchers.youtube_fetcher import YouTubeTranscriptFetcher
from evidence_ai.infrastructure.observability.logging import configure_logging
from evidence_ai.infrastructure.search.duckduckgo_provider import DuckDuckGoProvider
from evidence_ai.application.use_cases.verify_content import VerifyContentUseCase

logger = structlog.get_logger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    """Inicializa recursos al arrancar el worker."""
    settings = get_settings()
    configure_logging(level=settings.log_level, json_logs=settings.is_production)

    container = Container()
    await container.init_resources()
    ctx["container"] = container

    # Construir el orquestador (tiene muchas deps, lo hacemos a mano)
    ctx["verify_use_case"] = VerifyContentUseCase(
        uow_factory=container.unit_of_work,
        fetchers=[YouTubeTranscriptFetcher(), ReadabilityFetcher()],
        search_providers=[DuckDuckGoProvider()],
        ai_reasoner=ClaudeAIReasoner(settings=settings),
        event_publisher=container.event_publisher(),
        confidence_calculator=ConfidenceCalculator(),
        max_sources_per_claim=settings.max_sources_per_claim,
    )
    logger.info("worker_started")


async def shutdown(ctx: dict[str, Any]) -> None:
    container: Container = ctx["container"]
    await container.shutdown_resources()
    logger.info("worker_stopped")


async def run_verification(ctx: dict[str, Any], verification_id: str) -> None:
    """Tarea principal: ejecuta el pipeline de verificación."""
    use_case: VerifyContentUseCase = ctx["verify_use_case"]
    await use_case.execute(UUID(verification_id))


class WorkerSettings:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [run_verification]
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = settings.verification_timeout_seconds
    max_jobs = 5
    keep_result = 60 * 60 * 24  # 24h
