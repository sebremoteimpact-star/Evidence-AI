"""Modelo ORM: manipulation_signals — señales detectadas en el input."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.domain.value_objects.manipulation_signal import (
    ManipulationType,
    SignalSeverity,
)
from evidence_ai.infrastructure.persistence.models.base import Base, UuidPk

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.verification_model import (
        VerificationModel,
    )


class ManipulationSignalModel(Base):
    __tablename__ = "manipulation_signals"

    id: Mapped[UuidPk]
    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[ManipulationType] = mapped_column(
        SAEnum(ManipulationType, name="manipulation_type"), nullable=False
    )
    severity: Mapped[SignalSeverity] = mapped_column(
        SAEnum(SignalSeverity, name="signal_severity"), nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_passage: Mapped[str | None] = mapped_column(Text)

    verification: Mapped[VerificationModel] = relationship(
        back_populates="manipulation_signals"
    )
