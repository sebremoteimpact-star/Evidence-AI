"""Entidad Claim — una afirmación atómica extraída del input."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from evidence_ai.domain.value_objects.claim_type import ClaimType


@dataclass
class Claim:
    id: UUID
    verification_id: UUID
    position: int
    """Orden de aparición en el input original (0-indexed)."""

    text: str
    """Afirmación reformulada como oración autocontenida."""

    claim_type: ClaimType
    context: str | None
    """Contexto necesario para entender el claim sin leer el original."""

    keywords: list[str] = field(default_factory=list)
    """Términos clave para generar queries de búsqueda."""

    created_at: datetime | None = None
