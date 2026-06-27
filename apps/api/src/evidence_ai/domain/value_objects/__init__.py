"""Value objects del dominio — enums y tipos inmutables."""

from evidence_ai.domain.value_objects.claim_type import ClaimType
from evidence_ai.domain.value_objects.confidence_score import (
    ConfidenceFactor,
    ConfidenceScore,
    Verdict,
)
from evidence_ai.domain.value_objects.manipulation_signal import (
    ManipulationType,
    SignalSeverity,
)
from evidence_ai.domain.value_objects.source_tier import SourceTier
from evidence_ai.domain.value_objects.source_type import SourceType
from evidence_ai.domain.value_objects.stance import Stance
from evidence_ai.domain.value_objects.verification_status import (
    InputType,
    VerificationStatus,
)

__all__ = [
    "ClaimType",
    "ConfidenceFactor",
    "ConfidenceScore",
    "InputType",
    "ManipulationType",
    "SignalSeverity",
    "SourceTier",
    "SourceType",
    "Stance",
    "Verdict",
    "VerificationStatus",
]
