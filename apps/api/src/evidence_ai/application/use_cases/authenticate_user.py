"""Caso de uso: autenticar usuario con email + password."""

from __future__ import annotations

from dataclasses import dataclass

from evidence_ai.application.ports.repositories.user_repository import UserRepository
from evidence_ai.application.ports.unit_of_work import UnitOfWork
from evidence_ai.domain.entities import User


class InvalidCredentialsError(Exception):
    """Credenciales inválidas — mensaje genérico para no filtrar si el email existe."""


class InactiveUserError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticateUserCommand:
    email: str
    password: str


class AuthenticateUserUseCase:
    def __init__(self, uow: UnitOfWork, user_repo_factory, password_hasher) -> None:
        self._uow = uow
        self._user_repo_factory = user_repo_factory
        self._hasher = password_hasher

    async def execute(self, cmd: AuthenticateUserCommand) -> User:
        async with self._uow:
            user_repo: UserRepository = self._user_repo_factory(self._uow)
            user = await user_repo.get_by_email(cmd.email.lower().strip())

            if user is None or user.password_hash is None:
                # Tiempo constante: hash dummy para no filtrar la existencia
                self._hasher.verify(
                    "$argon2id$v=19$m=19456,t=2,p=1$dummysalt12345678$" + "x" * 43,
                    cmd.password,
                )
                raise InvalidCredentialsError("Email o contraseña incorrectos")

            if not self._hasher.verify(user.password_hash, cmd.password):
                raise InvalidCredentialsError("Email o contraseña incorrectos")

            if not user.is_active:
                raise InactiveUserError("La cuenta está desactivada")

            return user
