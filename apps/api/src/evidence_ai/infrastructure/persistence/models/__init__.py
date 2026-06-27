"""Modelos ORM de SQLAlchemy.

Importar TODOS los modelos aquí es necesario para que Alembic los descubra
al hacer autogenerate de migraciones.
"""

from evidence_ai.infrastructure.persistence.models.audit_log_model import AuditLogModel
from evidence_ai.infrastructure.persistence.models.base import Base
from evidence_ai.infrastructure.persistence.models.claim_model import ClaimModel
from evidence_ai.infrastructure.persistence.models.evidence_model import (
    EMBEDDING_DIM,
    EvidenceModel,
)
from evidence_ai.infrastructure.persistence.models.manipulation_signal_model import (
    ManipulationSignalModel,
)
from evidence_ai.infrastructure.persistence.models.report_model import ReportModel
from evidence_ai.infrastructure.persistence.models.source_model import SourceModel
from evidence_ai.infrastructure.persistence.models.user_model import UserModel
from evidence_ai.infrastructure.persistence.models.verification_event_model import (
    VerificationEventModel,
)
from evidence_ai.infrastructure.persistence.models.verification_model import (
    VerificationModel,
)

__all__ = [
    "EMBEDDING_DIM",
    "AuditLogModel",
    "Base",
    "ClaimModel",
    "EvidenceModel",
    "ManipulationSignalModel",
    "ReportModel",
    "SourceModel",
    "UserModel",
    "VerificationEventModel",
    "VerificationModel",
]
