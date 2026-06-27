"""Modelo ORM: evidence — pasaje de fuente que se relaciona con un claim."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, DateTime, Enum as SAEnum, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.domain.value_objects.stance import Stance
from evidence_ai.infrastructure.persistence.models.base import Base, UuidPk

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.claim_model import ClaimModel
    from evidence_ai.infrastructure.persistence.models.source_model import SourceModel

# Dimensión por defecto del embedding (Voyage-3-lite = 1024).
# Si cambias el modelo, ajusta esto Y genera una migración nueva.
EMBEDDING_DIM = 1024


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id: Mapped[UuidPk]
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    passage: Mapped[str] = mapped_column(Text, nullable=False)
    passage_hash: Mapped[str] = mapped_column(
        Text, nullable=False, index=True,
        comment="SHA-256 del pasaje normalizado, para dedupe",
    )
    stance: Mapped[Stance] = mapped_column(
        SAEnum(Stance, name="stance"), nullable=False, index=True
    )
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped[ClaimModel] = relationship(back_populates="evidence")
    source: Mapped[SourceModel] = relationship(back_populates="evidence")
