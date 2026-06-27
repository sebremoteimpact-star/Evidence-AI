"""Modelo ORM: verification_events — eventos del pipeline para SSE y replay."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import UUID, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.infrastructure.persistence.models.base import Base, UuidPk

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.verification_model import (
        VerificationModel,
    )


class VerificationEventModel(Base):
    """Cada paso del pipeline produce uno o más eventos persistidos aquí.

    Permite que un cliente que reconecta vía SSE haga replay de los eventos
    ya ocurridos antes de suscribirse al pubsub en vivo.
    """

    __tablename__ = "verification_events"

    id: Mapped[UuidPk]
    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    verification: Mapped[VerificationModel] = relationship(back_populates="events")
