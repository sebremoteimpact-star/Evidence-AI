"""Tipo concreto de fuente — informa al usuario qué clase de organismo es."""

from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    # Académico
    ACADEMIC_DATABASE = "academic_database"
    ACADEMIC_INDEX = "academic_index"
    ACADEMIC_API = "academic_api"
    ACADEMIC_METADATA = "academic_metadata"
    JOURNAL = "journal"
    PREPRINT = "preprint"

    # Oficial / gobierno
    COURT = "court"
    LEGISLATURE = "legislature"
    GOVERNMENT = "government"
    OPEN_DATA = "open_data"
    NATIONAL_STATISTICS = "national_statistics"
    CENTRAL_BANK = "central_bank"

    # Internacional
    INTERNATIONAL_ORG = "international_org"
    DATA_PLATFORM = "data_platform"

    # Fact-check
    FACTCHECK = "factcheck"

    # Académico secundario
    UNIVERSITY = "university"
    RESEARCH_INSTITUTE = "research_institute"
    THINK_TANK = "think_tank"

    # Periodismo
    NEWS_AGENCY = "news_agency"
    NEWS = "news"

    OTHER = "other"

    @property
    def label_es(self) -> str:
        return {
            "academic_database": "Base de datos académica",
            "academic_index": "Índice académico",
            "academic_api": "API académica",
            "academic_metadata": "Metadatos académicos",
            "journal": "Revista científica",
            "preprint": "Preprint (no peer-reviewed)",
            "court": "Tribunal",
            "legislature": "Legislatura",
            "government": "Gobierno",
            "open_data": "Datos abiertos",
            "national_statistics": "Estadísticas nacionales",
            "central_bank": "Banco central",
            "international_org": "Organismo internacional",
            "data_platform": "Plataforma de datos",
            "factcheck": "Fact-check",
            "university": "Universidad",
            "research_institute": "Instituto de investigación",
            "think_tank": "Think tank",
            "news_agency": "Agencia de noticias",
            "news": "Medio de comunicación",
            "other": "Otro",
        }[self.value]
