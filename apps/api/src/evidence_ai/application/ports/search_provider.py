"""Puerto: SearchProvider.

Cada proveedor (DuckDuckGo, Brave, Google CSE, PubMed, CrossRef, etc.)
implementa este Protocol. El CompositeSearchProvider hace fan-out a todos
los disponibles y deduplica resultados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SearchResult:
    """Un resultado bruto de una búsqueda."""

    url: str
    title: str
    snippet: str
    """Fragmento de la página tal como lo devuelve el motor de búsqueda."""

    provider: str
    """Nombre del proveedor que lo devolvió ('duckduckgo', 'pubmed', ...)."""

    published_at: datetime | None = None
    language: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SearchQuery:
    text: str
    language: str | None = None
    max_results: int = 10
    site: str | None = None
    """Filtrar a un dominio específico (ej: 'who.int')."""


class SearchProvider(Protocol):
    name: str

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        ...

    async def is_available(self) -> bool:
        """True si el proveedor tiene las credenciales necesarias y está saludable."""
        ...
