"""Clasificación de un claim según verificabilidad."""

from __future__ import annotations

from enum import Enum


class ClaimType(str, Enum):
    FACTUAL = "factual"
    """Afirmación factual verificable con evidencia (ej: 'X causó Y en 2024')."""

    OPINION = "opinion"
    """Juicio de valor subjetivo (ej: 'X es la mejor opción')."""

    PREDICTION = "prediction"
    """Afirmación sobre el futuro (no verificable hoy)."""

    NORMATIVE = "normative"
    """Afirmación sobre cómo deberían ser las cosas (ética/política)."""

    UNVERIFIABLE = "unverifiable"
    """Verificable en principio pero sin acceso a fuentes (ej: pensamiento privado)."""

    @property
    def label_es(self) -> str:
        return {
            "factual": "Factual",
            "opinion": "Opinión",
            "prediction": "Predicción",
            "normative": "Normativa",
            "unverifiable": "No verificable",
        }[self.value]

    @property
    def is_verifiable(self) -> bool:
        """Solo los claims FACTUAL se buscan en fuentes externas."""
        return self == ClaimType.FACTUAL
