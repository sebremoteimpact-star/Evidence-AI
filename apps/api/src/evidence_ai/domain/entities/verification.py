"""Entidad Verification — una solicitud de verificación de contenido."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from evidence_ai.domain.value_objects.verification_status import InputType, VerificationStatus


@dataclass
class Verification:
    id: UUID
    user_id: UUID
    input_type: InputType
    input_raw: str
    """Lo que pegó el usuario: URL, texto, ruta del archivo subido."""

    input_normalized: str | None
    """Texto canónico extraído por el ingestor (None hasta que se procese)."""

    source_url: str | None
    """URL original si el input era una URL."""

    language: str | None
    """Idioma detectado (ISO 639-1)."""

    status: VerificationStatus
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
