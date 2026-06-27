"""Schemas Pydantic para el reporte agregado completo."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from evidence_ai.domain.value_objects import (
    ClaimType,
    InputType,
    ManipulationType,
    SignalSeverity,
    SourceTier,
    SourceType,
    Stance,
    Verdict,
    VerificationStatus,
)


class SourceOut(BaseModel):
    id: UUID
    canonical_url: str
    domain: str
    title: str | None
    tier: SourceTier
    tier_label: str = Field(description="Etiqueta en español del tier")
    source_type: SourceType
    source_type_label: str
    published_at: datetime | None
    language: str | None
    methodology_notes: str | None


class EvidenceOut(BaseModel):
    id: UUID
    source: SourceOut
    passage: str
    stance: Stance
    stance_label: str
    relevance_score: float
    retrieved_at: datetime


class ClaimOut(BaseModel):
    id: UUID
    position: int
    text: str
    claim_type: ClaimType
    claim_type_label: str
    context: str | None
    keywords: list[str]
    evidence_supporting: list[EvidenceOut] = Field(default_factory=list)
    evidence_contradicting: list[EvidenceOut] = Field(default_factory=list)
    evidence_context: list[EvidenceOut] = Field(default_factory=list)
    confidence_score: int | None = None
    verdict: Verdict | None = None
    verdict_label: str | None = None
    confidence_factors: list[dict[str, Any]] = Field(default_factory=list)


class ManipulationSignalOut(BaseModel):
    id: UUID
    signal_type: ManipulationType
    signal_type_label: str
    severity: SignalSeverity
    severity_label: str
    explanation: str
    evidence_passage: str | None


class ReportSummaryOut(BaseModel):
    headline: str
    summary: str
    executive_conclusion: str
    confidence_value: int
    verdict: Verdict
    verdict_label: str
    language: str
    generated_at: datetime


class FullVerificationResponse(BaseModel):
    """Respuesta agregada con TODO lo necesario para renderizar el reporte completo."""

    id: UUID
    user_id: UUID
    input_type: InputType
    input_type_label: str
    input_raw: str
    input_normalized: str | None
    source_url: str | None
    language: str | None
    status: VerificationStatus
    status_label: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    report: ReportSummaryOut | None
    claims: list[ClaimOut]
    manipulation_signals: list[ManipulationSignalOut]

    stats: dict[str, int] = Field(
        description="Conteos agregados: total_claims, factual_claims, total_evidence, "
                    "n_supporting, n_contradicting, n_context, unique_domains, unique_tiers"
    )
