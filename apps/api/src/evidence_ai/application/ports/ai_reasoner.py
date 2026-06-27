"""Puerto: AIReasoner — abstracción sobre el LLM.

Implementación concreta: Claude API. Pero el dominio no sabe de Claude.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ExtractedClaim:
    text: str
    claim_type: str  # "factual" | "opinion" | "prediction" | "normative" | "unverifiable"
    context: str | None
    keywords: list[str]


@dataclass(frozen=True)
class ManipulationFinding:
    signal_type: str
    severity: str  # "low" | "medium" | "high"
    explanation: str
    evidence_passage: str | None


@dataclass(frozen=True)
class EvidenceJudgment:
    """Juicio sobre un pasaje recuperado, hecho por la IA."""

    source_url: str
    passage: str
    stance: str  # "supports" | "contradicts" | "context" | "unrelated"
    relevance_score: float


@dataclass(frozen=True)
class ClaimReasoning:
    """Razonamiento sintetizado de la IA sobre un claim, dado un set de evidencia."""

    summary: str
    supporting_evidence: list[EvidenceJudgment]
    contradicting_evidence: list[EvidenceJudgment]
    context_evidence: list[EvidenceJudgment]
    notes_on_contradictions: str | None


@dataclass(frozen=True)
class AIUsage:
    """Métricas de uso devueltas por la llamada (para audit_log)."""

    model: str
    tokens_input: int
    tokens_output: int


class AIReasoner(Protocol):
    async def extract_claims(
        self,
        content: str,
        language: str,
    ) -> tuple[list[ExtractedClaim], AIUsage]: ...

    async def detect_manipulation(
        self,
        content: str,
        language: str,
    ) -> tuple[list[ManipulationFinding], AIUsage]: ...

    async def generate_queries(
        self,
        claim_text: str,
        context: str | None,
        keywords: list[str],
        language: str,
    ) -> tuple[list[str], AIUsage]: ...

    async def reason_over_evidence(
        self,
        claim_text: str,
        claim_context: str | None,
        passages: list[dict[str, Any]],
        language: str,
    ) -> tuple[ClaimReasoning, AIUsage]: ...
