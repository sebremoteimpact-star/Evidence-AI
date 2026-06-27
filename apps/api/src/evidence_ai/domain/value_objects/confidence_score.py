"""Score de confianza — siempre con desglose auditable por factor.

La fórmula es **determinista**: NO la calcula Claude. Se calcula a partir de
la evidencia recuperada para que cada reporte sea reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    """Veredictos calibrados — JAMÁS afirman verdad o falsedad absoluta."""

    STRONGLY_SUPPORTED = "strongly_supported"
    """La evidencia disponible apoya fuertemente la afirmación."""

    SUPPORTED = "supported"
    """La evidencia disponible apoya la afirmación."""

    MIXED = "mixed"
    """La evidencia disponible es mixta: hay apoyo y contradicción significativos."""

    CONTRADICTED = "contradicted"
    """La evidencia disponible contradice la afirmación."""

    STRONGLY_CONTRADICTED = "strongly_contradicted"
    """La evidencia disponible contradice fuertemente la afirmación."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    """No se encontró evidencia suficiente para tomar postura."""

    @property
    def label_es(self) -> str:
        return {
            "strongly_supported": "La evidencia apoya fuertemente",
            "supported": "La evidencia apoya",
            "mixed": "La evidencia es mixta",
            "contradicted": "La evidencia contradice",
            "strongly_contradicted": "La evidencia contradice fuertemente",
            "insufficient_evidence": "Evidencia insuficiente",
        }[self.value]


@dataclass(frozen=True)
class ConfidenceFactor:
    """Un factor individual del score, con su peso y explicación."""

    name: str
    value: float  # 0.0 - 1.0
    weight: float  # 0.0 - 1.0
    explanation: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"value debe estar en [0, 1], recibido {self.value}")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"weight debe estar en [0, 1], recibido {self.weight}")


@dataclass(frozen=True)
class ConfidenceScore:
    """Score 0-100 con desglose por factor y veredicto calibrado."""

    value: int  # 0 - 100
    verdict: Verdict
    factors: tuple[ConfidenceFactor, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"value debe estar en [0, 100], recibido {self.value}")

    @property
    def display_es(self) -> str:
        return f"{self.value}/100 — {self.verdict.label_es}"
