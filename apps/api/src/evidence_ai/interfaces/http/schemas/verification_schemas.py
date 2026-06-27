"""Schemas Pydantic para verificaciones."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from evidence_ai.domain.value_objects import InputType, VerificationStatus


class CreateVerificationRequest(BaseModel):
    input_type: InputType
    input_raw: str = Field(min_length=1, max_length=50_000)


class VerificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    input_type: InputType
    input_raw: str
    input_normalized: str | None
    source_url: str | None
    language: str | None
    status: VerificationStatus
    status_label: str = Field(description="Etiqueta en el idioma del usuario")
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_entity(cls, entity) -> "VerificationResponse":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            input_type=entity.input_type,
            input_raw=entity.input_raw,
            input_normalized=entity.input_normalized,
            source_url=entity.source_url,
            language=entity.language,
            status=entity.status,
            status_label=entity.status.label_es,
            error_message=entity.error_message,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )


class VerificationListResponse(BaseModel):
    items: list[VerificationResponse]
    next_cursor: UUID | None
