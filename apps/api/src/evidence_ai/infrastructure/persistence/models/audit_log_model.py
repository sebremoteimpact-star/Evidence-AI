"""Modelo ORM: audit_log — registro inmutable de actividad sensible.

Sobrevive a la eliminación de usuarios y verificaciones. Útil para:
- Auditoría de costos (tokens de Claude usados).
- Investigación post-mortem de errores.
- Cumplimiento regulatorio.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from evidence_ai.infrastructure.persistence.models.base import Base, UuidPk


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[UuidPk]
    # Sin FK ondelete CASCADE — queremos retener el log aunque borren al usuario.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    verification_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    """Ej: 'verification.created', 'ai.claim_extracted', 'auth.login_failed'."""

    prompt_hash: Mapped[str | None] = mapped_column(String(64))
    """SHA-256 del prompt enviado (no el contenido, para no almacenar datos sensibles)."""

    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    cost_estimate_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))

    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
