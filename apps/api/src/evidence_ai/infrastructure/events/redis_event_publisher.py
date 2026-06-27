"""EventPublisher sobre Redis pubsub (alimenta SSE).

Doble destino:
1. Persiste el evento en `verification_events` (para replay si el cliente reconecta).
2. Publica en el canal pubsub `evidence-ai:verification:{id}` para los SSE en vivo.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from evidence_ai.infrastructure.persistence.models import VerificationEventModel


class RedisEventPublisher:
    """Publica eventos a Redis pubsub y los persiste en DB."""

    def __init__(
        self,
        redis: Redis,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._redis = redis
        self._session_factory = session_factory

    @staticmethod
    def channel_for(verification_id: UUID) -> str:
        return f"evidence-ai:verification:{verification_id}"

    async def publish(
        self,
        verification_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        envelope = {
            "event_type": event_type,
            "payload": payload,
            "ts": datetime.now(UTC).isoformat(),
        }
        message = json.dumps(envelope, default=str)

        # 1. Persistir (sesión independiente, no parte del UoW del caso de uso)
        async with self._session_factory() as session:
            event = VerificationEventModel(
                verification_id=verification_id,
                event_type=event_type,
                payload=payload,
            )
            session.add(event)
            await session.commit()

        # 2. Pubsub para SSE en vivo
        await self._redis.publish(self.channel_for(verification_id), message)
