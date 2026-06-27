"""Modelo ORM: reports — reporte ejecutivo final."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import UUID, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.domain.value_objects.confidence_score import Verdict
from evidence_ai.infrastructure.persistence.models.base import Base, UuidPk

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.verification_model import (
        VerificationModel,
    )


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("confidence_value >= 0 AND confidence_value <= 100", name="confidence_range"),
    )

    id: Mapped[UuidPk]
    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    executive_conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_value: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[Verdict] = mapped_column(
        SAEnum(Verdict, name="verdict"), nullable=False
    )
    confidence_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Lista de factores con name, value, weight, explanation",
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    verification: Mapped[VerificationModel] = relationship(back_populates="report")
