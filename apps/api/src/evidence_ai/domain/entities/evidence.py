"""Entidad Evidence — un pasaje de una fuente que se relaciona con un claim."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from evidence_ai.domain.value_objects.stance import Stance


@dataclass
class Evidence:
    id: UUID
    claim_id: UUID
    source_id: UUID
    passage: str
    """Cita exacta extraída de la fuente."""

    stance: Stance
    relevance_score: float
    """Score 0-1 de qué tan relevante es el pasaje al claim."""

    retrieved_at: datetime
    """Timestamp de cuando se recuperó esta evidencia (importante para auditoría)."""
