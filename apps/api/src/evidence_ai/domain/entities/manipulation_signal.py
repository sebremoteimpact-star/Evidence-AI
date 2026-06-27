"""Entidad ManipulationSignal — una señal detectada en el contenido original."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from evidence_ai.domain.value_objects.manipulation_signal import (
    ManipulationType,
    SignalSeverity,
)


@dataclass
class ManipulationSignal:
    id: UUID
    verification_id: UUID
    signal_type: ManipulationType
    severity: SignalSeverity
    explanation: str
    """Explicación didáctica de por qué se detectó la señal."""

    evidence_passage: str | None
    """Fragmento concreto del input que disparó la señal."""
