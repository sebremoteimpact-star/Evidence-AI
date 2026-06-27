"""Implementación SQL del VerificationRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select, update

from evidence_ai.domain.entities import Verification
from evidence_ai.domain.value_objects import VerificationStatus
from evidence_ai.infrastructure.persistence.mappers import (
    model_to_verification,
    verification_to_model,
)
from evidence_ai.infrastructure.persistence.models import VerificationModel
from evidence_ai.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


class SqlVerificationRepository:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    @property
    def _session(self):
        if self._uow.session is None:
            raise RuntimeError("UnitOfWork no está activo (usar 'async with uow:')")
        return self._uow.session

    async def get_by_id(self, verification_id: UUID) -> Verification | None:
        result = await self._session.execute(
            select(VerificationModel).where(VerificationModel.id == verification_id)
        )
        model = result.scalar_one_or_none()
        return model_to_verification(model) if model else None

    async def get_by_id_for_user(
        self, verification_id: UUID, user_id: UUID
    ) -> Verification | None:
        result = await self._session.execute(
            select(VerificationModel).where(
                VerificationModel.id == verification_id,
                VerificationModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return model_to_verification(model) if model else None

    async def list_for_user(
        self, user_id: UUID, limit: int = 20, cursor: UUID | None = None
    ) -> list[Verification]:
        stmt = (
            select(VerificationModel)
            .where(VerificationModel.user_id == user_id)
            .order_by(desc(VerificationModel.created_at))
            .limit(limit)
        )
        if cursor is not None:
            # cursor-based: el cursor es el id del último visto
            anchor = await self._session.execute(
                select(VerificationModel.created_at).where(VerificationModel.id == cursor)
            )
            anchor_ts = anchor.scalar_one_or_none()
            if anchor_ts is not None:
                stmt = stmt.where(VerificationModel.created_at < anchor_ts)

        result = await self._session.execute(stmt)
        return [model_to_verification(m) for m in result.scalars().all()]

    async def create(self, verification: Verification) -> Verification:
        model = verification_to_model(verification)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model_to_verification(model)

    async def update_status(
        self,
        verification_id: UUID,
        status: VerificationStatus,
        error_message: str | None = None,
    ) -> None:
        values: dict = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        await self._session.execute(
            update(VerificationModel)
            .where(VerificationModel.id == verification_id)
            .values(**values)
        )

    async def update(self, verification: Verification) -> Verification:
        result = await self._session.execute(
            select(VerificationModel).where(VerificationModel.id == verification.id)
        )
        model = result.scalar_one()
        model.input_normalized = verification.input_normalized
        model.source_url = verification.source_url
        model.language = verification.language
        model.status = verification.status
        model.error_message = verification.error_message
        model.completed_at = verification.completed_at
        await self._session.flush()
        await self._session.refresh(model)
        return model_to_verification(model)
