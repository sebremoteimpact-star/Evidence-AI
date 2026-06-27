"""Postura de un pasaje de evidencia respecto a un claim."""

from __future__ import annotations

from enum import Enum


class Stance(str, Enum):
    SUPPORTS = "supports"
    """El pasaje respalda la afirmación."""

    CONTRADICTS = "contradicts"
    """El pasaje contradice la afirmación."""

    CONTEXT = "context"
    """Aporta contexto relevante sin tomar postura clara."""

    UNRELATED = "unrelated"
    """No es relevante al claim (se descarta del cálculo)."""

    @property
    def label_es(self) -> str:
        return {
            "supports": "Apoya",
            "contradicts": "Contradice",
            "context": "Contexto",
            "unrelated": "No relacionado",
        }[self.value]
