"""Puerto: EventPublisher.

Publica eventos del pipeline a un bus (Redis pubsub en producción).
Los suscriptores son: persistencia (verification_events) y SSE endpoint.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class EventPublisher(Protocol):
    async def publish(
        self,
        verification_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None: ...
