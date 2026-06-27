"""Puerto: JobQueue — encola trabajos largos al worker."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class JobQueue(Protocol):
    async def enqueue_verification(self, verification_id: UUID) -> str:
        """Encola la ejecución del pipeline. Devuelve el job_id."""
        ...
