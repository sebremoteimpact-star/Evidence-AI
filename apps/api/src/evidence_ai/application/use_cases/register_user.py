"""Caso de uso: registrar usuario con email + password."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from evidence_ai.application.ports.repositories.user_repository import UserRepository
from evidence_ai.application.ports.unit_of_work import UnitOfWork
from evidence_ai.domain.entities import User


class UserAlreadyExistsError(Exception):
    pass


class WeakPasswordError(Exception):
    pass


@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    password: str
    name: str | None = None
    locale: str = "es"


class RegisterUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        user_repo_factory,  # callable: UoW -> UserRepository
        password_hasher,
    ) -> None:
        self._uow = uow
        self._user_repo_factory = user_repo_factory
        self._hasher = password_hasher

    async def execute(self, cmd: RegisterUserCommand) -> User:
        if len(cmd.password) < 10:
            raise WeakPasswordError("La contraseña debe tener al menos 10 caracteres")

        async with self._uow:
            user_repo: UserRepository = self._user_repo_factory(self._uow)

            existing = await user_repo.get_by_email(cmd.email.lower().strip())
            if existing is not None:
                raise UserAlreadyExistsError(
                    f"Ya existe una cuenta con el email {cmd.email}"
                )

            now = datetime.now(UTC)
            user = User(
                id=uuid4(),
                email=cmd.email.lower().strip(),
                name=cmd.name,
                password_hash=self._hasher.hash(cmd.password),
                oauth_provider=None,
                oauth_subject=None,
                locale=cmd.locale,
                is_active=True,
                is_admin=False,
                created_at=now,
                updated_at=now,
            )
            created = await user_repo.create(user)
            return created
