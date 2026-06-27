"""Estado de una verificación a lo largo del pipeline."""

from __future__ import annotations

from enum import Enum


class VerificationStatus(str, Enum):
    PENDING = "pending"
    """Creada, encolada al worker, sin procesar."""

    INGESTING = "ingesting"
    """Extrayendo texto canónico del input."""

    EXTRACTING_CLAIMS = "extracting_claims"
    """Claude está extrayendo claims."""

    DETECTING_MANIPULATION = "detecting_manipulation"
    """Análisis de señales de manipulación."""

    SEARCHING_EVIDENCE = "searching_evidence"
    """Búsqueda de evidencia en múltiples proveedores."""

    RANKING_EVIDENCE = "ranking_evidence"
    """Aplicando ranking por tier, frescura, etc."""

    REASONING = "reasoning"
    """Claude razonando sobre la evidencia recuperada."""

    COMPOSING_REPORT = "composing_report"
    """Generando el reporte final."""

    COMPLETED = "completed"
    """Reporte disponible."""

    FAILED = "failed"
    """Error fatal en el pipeline."""

    CANCELLED = "cancelled"
    """Cancelada por el usuario."""

    @property
    def is_terminal(self) -> bool:
        return self in (
            VerificationStatus.COMPLETED,
            VerificationStatus.FAILED,
            VerificationStatus.CANCELLED,
        )

    @property
    def is_active(self) -> bool:
        return not self.is_terminal

    @property
    def label_es(self) -> str:
        return {
            "pending": "En cola",
            "ingesting": "Procesando contenido",
            "extracting_claims": "Extrayendo afirmaciones",
            "detecting_manipulation": "Detectando manipulación",
            "searching_evidence": "Buscando evidencia",
            "ranking_evidence": "Evaluando fuentes",
            "reasoning": "Razonando sobre evidencia",
            "composing_report": "Componiendo reporte",
            "completed": "Completado",
            "failed": "Falló",
            "cancelled": "Cancelado",
        }[self.value]


class InputType(str, Enum):
    TEXT = "text"
    URL = "url"
    YOUTUBE = "youtube"
    UPLOAD_VIDEO = "upload_video"
    UPLOAD_PDF = "upload_pdf"
    SOCIAL_POST = "social_post"

    @property
    def label_es(self) -> str:
        return {
            "text": "Texto",
            "url": "URL",
            "youtube": "Video YouTube",
            "upload_video": "Video subido",
            "upload_pdf": "PDF",
            "social_post": "Publicación de red social",
        }[self.value]
