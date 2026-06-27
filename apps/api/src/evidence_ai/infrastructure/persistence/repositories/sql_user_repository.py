"""Implementación SQL del UserRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from evidence_ai.domain.entities import User
from evidence_ai.infrastructure.persistence.mappers import model_to_user, user_to_model
from evidence_ai.infrastructure.persistence.models import UserModel
from evidence_ai.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


class SqlUserRepository:
    """Implementa UserRepository (Protocol) sobre SQLAlchemy."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    @property
    def _session(self):
        if self._uow.session is None:
            raise RuntimeError("UnitOfWork no está activo (usar 'async with uow:')")
        return self._uow.session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return model_to_user(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return model_to_user(model) if model else None

    async def get_by_oauth(self, provider: str, subject: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.oauth_provider == provider,
                UserModel.oauth_subject == subject,
            )
        )
        model = result.scalar_one_or_none()
        return model_to_user(model) if model else None

    async def create(self, user: User) -> User:
        model = user_to_model(user)
        self._session.add(model)
        await self._session.flush()  # asigna id y created_at sin commit
        await self._session.refresh(model)
        return model_to_user(model)

    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one()
        model.email = user.email
        model.name = user.name
        model.password_hash = user.password_hash
        model.oauth_provider = user.oauth_provider
        model.oauth_subject = user.oauth_subject
        model.locale = user.locale
        model.is_active = user.is_active
        model.is_admin = user.is_admin
        await self._session.flush()
        await self._session.refresh(model)
        return model_to_user(model)
