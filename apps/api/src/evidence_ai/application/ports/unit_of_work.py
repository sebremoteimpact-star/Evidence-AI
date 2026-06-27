"""Puerto: Unit of Work.

Encapsula una transacción de la base de datos. Cada caso de uso abre uno,
hace su trabajo, y al salir hace commit (o rollback si hubo excepción).
"""

from __future__ import annotations

from typing import Protocol


class UnitOfWork(Protocol):
    """Contrato del UoW. La implementación concreta vive en infrastructure."""

    async def __aenter__(self) -> "UnitOfWork": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
