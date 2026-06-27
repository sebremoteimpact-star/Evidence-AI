"""Entidad Source — una fuente única identificada por URL canónica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from evidence_ai.domain.value_objects.source_tier import SourceTier
from evidence_ai.domain.value_objects.source_type import SourceType


@dataclass
class Source:
    id: UUID
    canonical_url: str
    domain: str
    title: str | None
    tier: SourceTier
    source_type: SourceType
    published_at: datetime | None
    language: str | None  # ISO 639-1
    methodology_notes: str | None
    """Notas sobre transparencia metodológica (ej: 'preprint — no peer-reviewed')."""

    content_hash: str
    """SHA-256 del contenido extraído — para deduplicación entre verificaciones."""

    first_seen_at: datetime
