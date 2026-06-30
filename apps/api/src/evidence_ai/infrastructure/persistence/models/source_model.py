"""Modelo ORM: sources — fuente única identificada por URL canónica."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.domain.value_objects.source_tier import SourceTier
from evidence_ai.domain.value_objects.source_type import SourceType
from evidence_ai.infrastructure.persistence.models.base import Base, UuidPk

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.evidence_model import EvidenceModel


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[UuidPk]
    canonical_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[SourceTier] = mapped_column(
        SAEnum(SourceTier, name="source_tier", values_callable=lambda x: [str(e.value) for e in x]),
        nullable=False,
        index=True,
    )
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    language: Mapped[str | None] = mapped_column(String(5))
    methodology_notes: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evidence: Mapped[list[EvidenceModel]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
