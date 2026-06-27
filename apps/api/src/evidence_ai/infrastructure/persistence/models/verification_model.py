"""Modelo ORM: verifications — solicitud de verificación."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.domain.value_objects.verification_status import (
    InputType,
    VerificationStatus,
)
from evidence_ai.infrastructure.persistence.models.base import (
    Base,
    TimestampMixin,
    UuidPk,
)

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.claim_model import ClaimModel
    from evidence_ai.infrastructure.persistence.models.manipulation_signal_model import (
        ManipulationSignalModel,
    )
    from evidence_ai.infrastructure.persistence.models.report_model import ReportModel
    from evidence_ai.infrastructure.persistence.models.user_model import UserModel
    from evidence_ai.infrastructure.persistence.models.verification_event_model import (
        VerificationEventModel,
    )


class VerificationModel(Base, TimestampMixin):
    __tablename__ = "verifications"

    id: Mapped[UuidPk]
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input_type: Mapped[InputType] = mapped_column(
        SAEnum(InputType, name="input_type"), nullable=False
    )
    input_raw: Mapped[str] = mapped_column(Text, nullable=False)
    input_normalized: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(5))
    status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, name="verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[UserModel] = relationship(back_populates="verifications")
    claims: Mapped[list[ClaimModel]] = relationship(
        back_populates="verification",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    manipulation_signals: Mapped[list[ManipulationSignalModel]] = relationship(
        back_populates="verification",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events: Mapped[list[VerificationEventModel]] = relationship(
        back_populates="verification",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    report: Mapped[ReportModel | None] = relationship(
        back_populates="verification",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
