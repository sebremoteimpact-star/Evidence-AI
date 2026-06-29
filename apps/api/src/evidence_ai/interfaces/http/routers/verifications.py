"""Endpoints de verificaciones."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from evidence_ai.application.use_cases.create_verification import (
    CreateVerificationCommand,
    CreateVerificationUseCase,
)
from evidence_ai.config.container import Container
from evidence_ai.domain.value_objects import Stance
from evidence_ai.infrastructure.persistence.models import (
    ClaimModel,
    EvidenceModel,
    ManipulationSignalModel,
    ReportModel,
    SourceModel,
    VerificationModel,
)
from evidence_ai.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from evidence_ai.infrastructure.persistence.repositories.sql_verification_repository import (
    SqlVerificationRepository,
)
from evidence_ai.interfaces.http.dependencies import CurrentUserId
from evidence_ai.interfaces.http.schemas.report_schemas import (
    ClaimOut,
    EvidenceOut,
    FullVerificationResponse,
    ManipulationSignalOut,
    ReportSummaryOut,
    SourceOut,
)
from evidence_ai.interfaces.http.schemas.verification_schemas import (
    CreateVerificationRequest,
    VerificationListResponse,
    VerificationResponse,
)

router = APIRouter(prefix="/api/v1/verifications", tags=["verifications"])


@router.post(
    "",
    response_model=VerificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Crear verificación (asíncrona)",
)
@inject
async def create_verification(
    body: CreateVerificationRequest,
    user_id: CurrentUserId,
    use_case: CreateVerificationUseCase = Depends(Provide[Container.create_verification_use_case]),
) -> VerificationResponse:
    """Crea una verificación en estado `pending` y la encola al worker.
    Use el endpoint `/stream/{id}` para recibir progreso en vivo vía SSE.
    """
    verification = await use_case.execute(
        CreateVerificationCommand(
            user_id=user_id,
            input_type=body.input_type,
            input_raw=body.input_raw,
        )
    )
    return VerificationResponse.from_entity(verification)


@router.get(
    "/{verification_id}",
    response_model=VerificationResponse,
    summary="Obtener una verificación",
)
@inject
async def get_verification(
    verification_id: UUID,
    user_id: CurrentUserId,
    uow_factory: type[SqlAlchemyUnitOfWork] = Depends(Provide[Container.unit_of_work.provider]),
) -> VerificationResponse:
    uow = uow_factory()
    async with uow:
        repo = SqlVerificationRepository(uow)
        verification = await repo.get_by_id_for_user(verification_id, user_id)
    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verificación no encontrada"
        )
    return VerificationResponse.from_entity(verification)


@router.get(
    "",
    response_model=VerificationListResponse,
    summary="Listar verificaciones del usuario",
)
@inject
async def list_verifications(
    user_id: CurrentUserId,
    limit: int = 20,
    cursor: UUID | None = None,
    uow_factory: type[SqlAlchemyUnitOfWork] = Depends(Provide[Container.unit_of_work.provider]),
) -> VerificationListResponse:
    uow = uow_factory()
    async with uow:
        repo = SqlVerificationRepository(uow)
        items = await repo.list_for_user(user_id, limit=min(limit, 100), cursor=cursor)
    next_cursor = items[-1].id if len(items) == limit else None
    return VerificationListResponse(
        items=[VerificationResponse.from_entity(v) for v in items],
        next_cursor=next_cursor,
    )


def _source_to_out(s: SourceModel) -> SourceOut:
    return SourceOut(
        id=s.id,
        canonical_url=s.canonical_url,
        domain=s.domain,
        title=s.title,
        tier=s.tier,
        tier_label=s.tier.label_es,
        source_type=s.source_type,
        source_type_label=s.source_type.label_es,
        published_at=s.published_at,
        language=s.language,
        methodology_notes=s.methodology_notes,
    )


def _evidence_to_out(e: EvidenceModel) -> EvidenceOut:
    return EvidenceOut(
        id=e.id,
        source=_source_to_out(e.source),
        passage=e.passage,
        stance=e.stance,
        stance_label=e.stance.label_es,
        relevance_score=e.relevance_score,
        retrieved_at=e.retrieved_at,
    )


@router.get(
    "/{verification_id}/full",
    response_model=FullVerificationResponse,
    summary="Reporte completo agregado (verificación + claims + evidencia + señales)",
)
@inject
async def get_full_verification(
    verification_id: UUID,
    user_id: CurrentUserId,
    session_factory: Any = Depends(Provide[Container.session_factory]),
) -> FullVerificationResponse:
    """Devuelve TODO lo necesario para renderizar el reporte en una sola query.

    Esto evita N+1 desde el frontend. Usa selectinload para traer claims +
    evidencia + sources + manipulation_signals + report en pocas queries.
    """
    async with session_factory() as session:
        stmt = (
            select(VerificationModel)
            .where(
                VerificationModel.id == verification_id,
                VerificationModel.user_id == user_id,
            )
            .options(
                selectinload(VerificationModel.report),
                selectinload(VerificationModel.manipulation_signals),
                selectinload(VerificationModel.claims)
                .selectinload(ClaimModel.evidence)
                .selectinload(EvidenceModel.source),
            )
        )
        result = await session.execute(stmt)
        v: VerificationModel | None = result.scalar_one_or_none()

    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verificación no encontrada"
        )

    # Construir el desglose por claim
    report_breakdown_per_claim: dict[str, dict] = {}
    if v.report and v.report.confidence_breakdown:
        report_breakdown_per_claim = v.report.confidence_breakdown.get("per_claim", {})

    claims_out: list[ClaimOut] = []
    total_supports = total_contradicts = total_context = 0
    unique_domains: set[str] = set()
    unique_tiers: set[int] = set()
    total_evidence = 0

    for c in sorted(v.claims, key=lambda x: x.position):
        supports = [_evidence_to_out(e) for e in c.evidence if e.stance == Stance.SUPPORTS]
        contradicts = [_evidence_to_out(e) for e in c.evidence if e.stance == Stance.CONTRADICTS]
        context_ev = [_evidence_to_out(e) for e in c.evidence if e.stance == Stance.CONTEXT]

        total_supports += len(supports)
        total_contradicts += len(contradicts)
        total_context += len(context_ev)
        total_evidence += len(c.evidence)
        for e in c.evidence:
            unique_domains.add(e.source.domain)
            unique_tiers.add(int(e.source.tier))

        breakdown = report_breakdown_per_claim.get(str(c.id), {})
        verdict_val = breakdown.get("verdict")
        from evidence_ai.domain.value_objects import Verdict
        verdict_obj = Verdict(verdict_val) if verdict_val else None

        claims_out.append(ClaimOut(
            id=c.id,
            position=c.position,
            text=c.text,
            claim_type=c.claim_type,
            claim_type_label=c.claim_type.label_es,
            context=c.context,
            keywords=c.keywords,
            evidence_supporting=supports,
            evidence_contradicting=contradicts,
            evidence_context=context_ev,
            confidence_score=breakdown.get("value"),
            verdict=verdict_obj,
            verdict_label=verdict_obj.label_es if verdict_obj else None,
            confidence_factors=breakdown.get("factors", []),
        ))

    signals_out = [
        ManipulationSignalOut(
            id=s.id,
            signal_type=s.signal_type,
            signal_type_label=s.signal_type.label_es,
            severity=s.severity,
            severity_label=s.severity.label_es,
            explanation=s.explanation,
            evidence_passage=s.evidence_passage,
        )
        for s in v.manipulation_signals
    ]

    report_out: ReportSummaryOut | None = None
    if v.report:
        report_out = ReportSummaryOut(
            headline=v.report.headline,
            summary=v.report.summary,
            executive_conclusion=v.report.executive_conclusion,
            confidence_value=v.report.confidence_value,
            verdict=v.report.verdict,
            verdict_label=v.report.verdict.label_es,
            language=v.report.language,
            generated_at=v.report.generated_at,
        )

    return FullVerificationResponse(
        id=v.id,
        user_id=v.user_id,
        input_type=v.input_type,
        input_type_label=v.input_type.label_es,
        input_raw=v.input_raw,
        input_normalized=v.input_normalized,
        source_url=v.source_url,
        language=v.language,
        status=v.status,
        status_label=v.status.label_es,
        error_message=v.error_message,
        created_at=v.created_at,
        completed_at=v.completed_at,
        report=report_out,
        claims=claims_out,
        manipulation_signals=signals_out,
        stats={
            "total_claims": len(claims_out),
            "factual_claims": sum(1 for c in claims_out if c.claim_type.value == "factual"),
            "total_evidence": total_evidence,
            "n_supporting": total_supports,
            "n_contradicting": total_contradicts,
            "n_context": total_context,
            "unique_domains": len(unique_domains),
            "unique_tiers": len(unique_tiers),
            "manipulation_signals": len(signals_out),
        },
    )
