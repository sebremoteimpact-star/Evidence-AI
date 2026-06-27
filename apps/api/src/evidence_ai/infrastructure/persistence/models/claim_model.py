"""Modelo ORM: claims."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Enum as SAEnum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.domain.value_objects.claim_type import ClaimType
from evidence_ai.infrastructure.persistence.models.base import (
    Base,
    TimestampMixin,
    UuidPk,
)

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.evidence_model import EvidenceModel
    from evidence_ai.infrastructure.persistence.models.verification_model import (
        VerificationModel,
    )


class ClaimModel(Base, TimestampMixin):
    __tablename__ = "claims"

    id: Mapped[UuidPk]
    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[ClaimType] = mapped_column(
        SAEnum(ClaimType, name="claim_type"), nullable=False, index=True
    )
    context: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)

    verification: Mapped[VerificationModel] = relationship(back_populates="claims")
    evidence: Mapped[list[EvidenceModel]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
