"""Endpoints de verificaciones."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from evidence_ai.application.use_cases.create_verification import (
    CreateVerificationCommand,
    CreateVerificationUseCase,
)
from evidence_ai.config.container import Container
from evidence_ai.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from evidence_ai.infrastructure.persistence.repositories.sql_verification_repository import (
    SqlVerificationRepository,
)
from evidence_ai.interfaces.http.dependencies import CurrentUserId
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
    use_case: Annotated[
        CreateVerificationUseCase,
        Depends(Provide[Container.create_verification_use_case]),
    ],
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
    uow_factory: Annotated[
        type[SqlAlchemyUnitOfWork], Depends(Provide[Container.unit_of_work.provider])
    ],
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
    uow_factory: Annotated[
        type[SqlAlchemyUnitOfWork], Depends(Provide[Container.unit_of_work.provider])
    ] = None,
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
