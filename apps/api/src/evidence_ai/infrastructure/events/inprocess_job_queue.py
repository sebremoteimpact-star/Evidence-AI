"""Job queue in-process — ejecuta el pipeline dentro del mismo proceso del API.

Alternativa a arq cuando no hay worker separado (ej: Render free tier).

Trade-offs:
- ✅ Cero infraestructura extra
- ✅ Funciona en cualquier free tier
- ❌ Si el proceso reinicia, jobs en vuelo se pierden
- ❌ Comparte recursos con el API (CPU/RAM)

Acepta el riesgo porque en free tier el proceso duerme tras inactividad
de todas formas — la situación es equivalente.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


class InProcessJobQueue:
    """Implementa JobQueue ejecutando los pipelines como asyncio tasks."""

    def __init__(self, use_case_provider: Callable) -> None:
        """
        Args:
            use_case_provider: callable que devuelve una instancia de
                VerifyContentUseCase (típicamente el provider del container).
        """
        self._use_case_provider = use_case_provider
        self._tasks: set[asyncio.Task] = set()

    async def enqueue_verification(self, verification_id: UUID) -> str:
        use_case = self._use_case_provider()
        task = asyncio.create_task(self._safe_run(use_case, verification_id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return f"inprocess:{verification_id}"

    async def _safe_run(self, use_case, verification_id: UUID) -> None:
        try:
            await use_case.execute(verification_id)
        except Exception:
            logger.exception(
                "inprocess_pipeline_failed", verification_id=str(verification_id)
            )

    async def shutdown(self, timeout: float = 30.0) -> None:
        """Espera a que terminen los jobs en vuelo (con timeout)."""
        if not self._tasks:
            return
        logger.info("inprocess_shutdown_waiting", n_tasks=len(self._tasks))
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("inprocess_shutdown_timeout", n_tasks=len(self._tasks))
