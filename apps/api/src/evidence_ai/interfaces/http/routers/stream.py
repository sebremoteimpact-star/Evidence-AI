"""Endpoint SSE para streaming de progreso de verificación en vivo.

Estrategia:
  1. Al conectar, replay de eventos persistidos (por si el cliente reconecta).
  2. Después, suscripción al canal pubsub Redis del que el worker publica.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sse_starlette.sse import EventSourceResponse

from evidence_ai.config.container import Container
from evidence_ai.infrastructure.events.redis_event_publisher import RedisEventPublisher
from evidence_ai.infrastructure.persistence.models import (
    VerificationEventModel,
    VerificationModel,
)
from evidence_ai.interfaces.http.dependencies import CurrentUserIdSse

router = APIRouter(prefix="/api/v1/stream", tags=["stream"])


async def _replay_events(
    verification_id: UUID,
    session_factory: async_sessionmaker[AsyncSession],
    since_seq: int = 0,
) -> AsyncIterator[dict]:
    """Yields eventos persistidos en orden cronológico."""
    async with session_factory() as session:
        stmt = (
            select(VerificationEventModel)
            .where(VerificationEventModel.verification_id == verification_id)
            .order_by(VerificationEventModel.created_at)
            .offset(since_seq)
        )
        result = await session.execute(stmt)
        for event in result.scalars().all():
            yield {
                "event": event.event_type,
                "data": json.dumps({
                    "payload": event.payload,
                    "ts": event.created_at.isoformat(),
                }, default=str),
            }


async def _subscribe_live(
    verification_id: UUID, redis: Redis
) -> AsyncIterator[dict]:
    """Yields eventos en vivo del pubsub Redis hasta recibir un terminal."""
    channel = RedisEventPublisher.channel_for(verification_id)
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
            if msg is None:
                # heartbeat (mantiene conexión viva detrás de proxies)
                yield {"event": "ping", "data": "{}"}
                continue
            try:
                data = msg["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                envelope = json.loads(data)
                event_type = envelope.get("event_type", "message")
                yield {
                    "event": event_type,
                    "data": json.dumps({
                        "payload": envelope.get("payload", {}),
                        "ts": envelope.get("ts"),
                    }, default=str),
                }
                if event_type in ("completed", "failed", "cancelled"):
                    break
            except Exception:
                continue
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


@router.get("/{verification_id}", summary="Stream de progreso (SSE)")
@inject
async def stream_verification(
    verification_id: UUID,
    user_id: CurrentUserIdSse,
    redis: Annotated[Redis, Depends(Provide[Container.redis])],
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(Provide[Container.session_factory])
    ],
    since: int = Query(default=0, ge=0, description="Replay desde el N-ésimo evento"),
):
    """Stream Server-Sent Events del progreso de una verificación.

    El cliente puede pasar `?since=N` para reconectar y omitir N eventos ya vistos.
    """
    # Autorización: solo el dueño puede ver el stream
    async with session_factory() as session:
        result = await session.execute(
            select(VerificationModel.id).where(
                VerificationModel.id == verification_id,
                VerificationModel.user_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Verificación no encontrada"
            )

    async def event_gen() -> AsyncIterator[dict]:
        # 1. Replay
        replayed = 0
        async for ev in _replay_events(verification_id, session_factory, since_seq=since):
            yield ev
            replayed += 1

        # Si ya terminó, no nos suscribimos
        async with session_factory() as session:
            v = (await session.execute(
                select(VerificationModel.status).where(
                    VerificationModel.id == verification_id
                )
            )).scalar_one()
        if v in ("completed", "failed", "cancelled"):
            yield {"event": "end", "data": json.dumps({"reason": "already_finished"})}
            return

        # 2. Stream en vivo
        async for ev in _subscribe_live(verification_id, redis):
            yield ev

    return EventSourceResponse(event_gen())
