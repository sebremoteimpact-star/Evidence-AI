"""Entidades del dominio — modelos puros sin frameworks."""

from evidence_ai.domain.entities.claim import Claim
from evidence_ai.domain.entities.evidence import Evidence
from evidence_ai.domain.entities.manipulation_signal import ManipulationSignal
from evidence_ai.domain.entities.report import Report
from evidence_ai.domain.entities.source import Source
from evidence_ai.domain.entities.user import User
from evidence_ai.domain.entities.verification import Verification

__all__ = [
    "Claim",
    "Evidence",
    "ManipulationSignal",
    "Report",
    "Source",
    "User",
    "Verification",
]
