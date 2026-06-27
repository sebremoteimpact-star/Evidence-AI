"""Mapper Verification ↔ VerificationModel."""

from __future__ import annotations

from evidence_ai.domain.entities import Verification
from evidence_ai.infrastructure.persistence.models import VerificationModel


def model_to_verification(model: VerificationModel) -> Verification:
    return Verification(
        id=model.id,
        user_id=model.user_id,
        input_type=model.input_type,
        input_raw=model.input_raw,
        input_normalized=model.input_normalized,
        source_url=model.source_url,
        language=model.language,
        status=model.status,
        error_message=model.error_message,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )


def verification_to_model(entity: Verification) -> VerificationModel:
    return VerificationModel(
        id=entity.id,
        user_id=entity.user_id,
        input_type=entity.input_type,
        input_raw=entity.input_raw,
        input_normalized=entity.input_normalized,
        source_url=entity.source_url,
        language=entity.language,
        status=entity.status,
        error_message=entity.error_message,
        completed_at=entity.completed_at,
    )
