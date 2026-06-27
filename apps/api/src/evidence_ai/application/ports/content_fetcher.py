"""Puerto: ContentFetcher — descarga y extracción de contenido canónico."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class FetchedContent:
    canonical_url: str
    title: str | None
    text: str
    """Texto canónico extraído (sin nav, footer, etc.)."""

    published_at: datetime | None
    language: str | None
    raw_html: str | None = None
    is_paywalled: bool = False
    fetched_at: datetime | None = None


class ContentFetcher(Protocol):
    async def fetch(self, url: str) -> FetchedContent: ...
    async def can_handle(self, url: str) -> bool: ...
