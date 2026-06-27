"""Tiers de fuentes — jerarquía de evidencia.

El sistema prioriza evidencia primaria sobre secundaria. Cada fuente recibe un tier
del 1 al 6 según su nivel de transparencia metodológica e independencia.
"""

from __future__ import annotations

from enum import IntEnum


class SourceTier(IntEnum):
    """Tier 1 es el más fuerte, tier 6 el más débil.

    El score numérico se usa directamente en cálculos de ranking
    (menor número = mayor peso en confianza).
    """

    PEER_REVIEWED = 1
    """Papers peer-reviewed, bases académicas (PubMed, CrossRef, Semantic Scholar)."""

    OFFICIAL = 2
    """Documentos oficiales: cortes, legislaturas, estadísticas nacionales, bancos centrales."""

    INTERNATIONAL_ORG = 3
    """Organizaciones internacionales con metodología pública (WHO, UN, OECD, World Bank)."""

    FACT_CHECKER = 4
    """Fact-checkers IFCN-certified (PolitiFact, FactCheck.org, Maldita, AFP Fact Check)."""

    ACADEMIC = 5
    """Universidades, think tanks con financiación transparente."""

    JOURNALISM = 6
    """Periodismo profesional — solo cuando no hay evidencia primaria."""

    @property
    def label_es(self) -> str:
        return {
            1: "Peer-reviewed",
            2: "Documento oficial",
            3: "Organismo internacional",
            4: "Fact-checker",
            5: "Académico / Think tank",
            6: "Periodismo",
        }[self.value]

    @property
    def weight(self) -> float:
        """Peso base para el cálculo de confianza (0..1)."""
        return {1: 1.0, 2: 0.92, 3: 0.85, 4: 0.75, 5: 0.65, 6: 0.50}[self.value]
