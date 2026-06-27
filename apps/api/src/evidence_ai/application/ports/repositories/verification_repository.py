"""Puerto: VerificationRepository."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from evidence_ai.domain.entities import Verification
from evidence_ai.domain.value_objects import VerificationStatus


class VerificationRepository(Protocol):
    async def get_by_id(self, verification_id: UUID) -> Verification | None: ...
    async def get_by_id_for_user(
        self, verification_id: UUID, user_id: UUID
    ) -> Verification | None: ...
    async def list_for_user(
        self, user_id: UUID, limit: int = 20, cursor: UUID | None = None
    ) -> list[Verification]: ...
    async def create(self, verification: Verification) -> Verification: ...
    async def update_status(
        self,
        verification_id: UUID,
        status: VerificationStatus,
        error_message: str | None = None,
    ) -> None: ...
    async def update(self, verification: Verification) -> Verification: ...
