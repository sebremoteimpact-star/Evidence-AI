"""Cola de jobs sobre arq (Redis-backed, async-native)."""

from __future__ import annotations

from uuid import UUID

from arq import ArqRedis


class ArqJobQueue:
    """Encola jobs al worker arq."""

    def __init__(self, redis: ArqRedis) -> None:
        self._redis = redis

    async def enqueue_verification(self, verification_id: UUID) -> str:
        job = await self._redis.enqueue_job(
            "run_verification",
            str(verification_id),
            _job_id=f"verification:{verification_id}",
            _defer_by=None,
        )
        if job is None:
            raise RuntimeError("No se pudo encolar el job de verificación")
        return job.job_id
