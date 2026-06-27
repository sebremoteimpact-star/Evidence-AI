"""Señales de manipulación detectadas en el contenido original.

Estas señales NO determinan si el contenido es verdadero o falso.
Indican técnicas retóricas o formales que el usuario debería tener en cuenta
al evaluar el contenido didácticamente.
"""

from __future__ import annotations

from enum import Enum


class ManipulationType(str, Enum):
    EMOTIONAL_LANGUAGE = "emotional_language"
    """Lenguaje fuertemente cargado emocionalmente."""

    CLICKBAIT = "clickbait"
    """Titular sensacionalista que no se cumple en el cuerpo."""

    PROPAGANDA = "propaganda"
    """Técnicas clásicas de propaganda (apelación a la autoridad, ad hominem, ...)."""

    MISLEADING_HEADLINE = "misleading_headline"
    """El titular contradice o exagera respecto al cuerpo."""

    MANIPULATED_STATS = "manipulated_stats"
    """Estadísticas presentadas sin contexto, escala manipulada, etc."""

    CONTEXT_MANIPULATION = "context_manipulation"
    """Hechos reales presentados fuera de su contexto crítico."""

    AI_GENERATED = "ai_generated"
    """Indicadores de generación por IA (patrones léxicos, ausencia de errores típicos humanos)."""

    DEEPFAKE_INDICATOR = "deepfake_indicator"
    """Solo para video: inconsistencias en metadata o transcript que sugieren manipulación."""

    @property
    def label_es(self) -> str:
        return {
            "emotional_language": "Lenguaje emocional",
            "clickbait": "Clickbait",
            "propaganda": "Propaganda",
            "misleading_headline": "Titular engañoso",
            "manipulated_stats": "Estadísticas manipuladas",
            "context_manipulation": "Manipulación de contexto",
            "ai_generated": "Generado por IA",
            "deepfake_indicator": "Indicador de deepfake",
        }[self.value]


class SignalSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def label_es(self) -> str:
        return {"low": "Baja", "medium": "Media", "high": "Alta"}[self.value]
