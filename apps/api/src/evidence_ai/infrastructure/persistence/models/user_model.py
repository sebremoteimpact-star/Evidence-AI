"""Modelo ORM: users."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evidence_ai.infrastructure.persistence.models.base import (
    Base,
    TimestampMixin,
    UuidPk,
)

if TYPE_CHECKING:
    from evidence_ai.infrastructure.persistence.models.verification_model import (
        VerificationModel,
    )


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UuidPk]
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    oauth_provider: Mapped[str | None] = mapped_column(String(50))
    oauth_subject: Mapped[str | None] = mapped_column(String(255), index=True)
    locale: Mapped[str] = mapped_column(String(5), default="es", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    verifications: Mapped[list[VerificationModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
