"""Entidad Report — el reporte ejecutivo generado al final del pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from evidence_ai.domain.value_objects.confidence_score import ConfidenceScore


@dataclass
class Report:
    id: UUID
    verification_id: UUID
    headline: str
    """Titular generado a partir del contenido original."""

    summary: str
    """Resumen ejecutivo de 2-3 oraciones."""

    executive_conclusion: str
    """Conclusión calibrada en lenguaje no-judicativo (ver Verdict)."""

    confidence: ConfidenceScore
    """Score global con desglose por factor."""

    language: str
    """Idioma del reporte (ISO 639-1) — siempre el del usuario."""

    generated_at: datetime
