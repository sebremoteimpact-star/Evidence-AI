"""Caso de uso: crear una verificación nueva y encolarla al worker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from evidence_ai.application.ports.job_queue import JobQueue
from evidence_ai.application.ports.repositories.verification_repository import (
    VerificationRepository,
)
from evidence_ai.application.ports.unit_of_work import UnitOfWork
from evidence_ai.domain.entities import Verification
from evidence_ai.domain.value_objects import InputType, VerificationStatus


class InputTooLargeError(Exception):
    pass


class InvalidInputError(Exception):
    pass


@dataclass(frozen=True)
class CreateVerificationCommand:
    user_id: UUID
    input_type: InputType
    input_raw: str
    """URL, texto bruto, o ruta del archivo subido (según input_type)."""


class CreateVerificationUseCase:
    """Crea la verificación en estado PENDING y la encola al worker."""

    def __init__(
        self,
        uow: UnitOfWork,
        verification_repo_factory,
        job_queue: JobQueue,
        max_input_chars: int,
    ) -> None:
        self._uow = uow
        self._verification_repo_factory = verification_repo_factory
        self._job_queue = job_queue
        self._max_input_chars = max_input_chars

    async def execute(self, cmd: CreateVerificationCommand) -> Verification:
        # Validación temprana de tamaño
        if len(cmd.input_raw) > self._max_input_chars:
            raise InputTooLargeError(
                f"El input excede el máximo de {self._max_input_chars} caracteres"
            )
        if not cmd.input_raw.strip():
            raise InvalidInputError("El input está vacío")

        # source_url se setea si es URL
        source_url = cmd.input_raw if cmd.input_type in (InputType.URL, InputType.YOUTUBE) else None

        async with self._uow:
            repo: VerificationRepository = self._verification_repo_factory(self._uow)
            now = datetime.now(UTC)
            verification = Verification(
                id=uuid4(),
                user_id=cmd.user_id,
                input_type=cmd.input_type,
                input_raw=cmd.input_raw,
                input_normalized=None,
                source_url=source_url,
                language=None,
                status=VerificationStatus.PENDING,
                error_message=None,
                created_at=now,
                completed_at=None,
            )
            created = await repo.create(verification)

        # Encolar después de commitear — si la cola falla, la verificación queda PENDING
        # y un worker scheduler podría rescatarla. Por ahora propagamos el error.
        await self._job_queue.enqueue_verification(created.id)
        return created
