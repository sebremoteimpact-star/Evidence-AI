"""Fetcher de URLs HTML con extracción de texto canónico vía trafilatura.

trafilatura es más robusto que readability para extracción multilingual.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import structlog
import trafilatura
from langdetect import LangDetectException, detect

from evidence_ai.application.ports.content_fetcher import FetchedContent
from evidence_ai.infrastructure.fetchers.ssrf_guard import SSRFBlocked, assert_url_is_safe

logger = structlog.get_logger(__name__)

USER_AGENT = "Evidence-AI/0.1 (+https://github.com/evidence-ai; open-source verification platform)"


class ReadabilityFetcher:
    """Fetcher genérico de URLs HTML."""

    def __init__(self, timeout: float = 10.0, max_bytes: int = 5_000_000) -> None:
        self._timeout = timeout
        self._max_bytes = max_bytes

    async def can_handle(self, url: str) -> bool:
        # Maneja cualquier http/https que no sea YouTube/PDF (esos tienen fetchers dedicados)
        lower = url.lower()
        return lower.startswith(("http://", "https://")) and not any(
            tag in lower for tag in ("youtube.com/watch", "youtu.be/", ".pdf")
        )

    async def fetch(self, url: str) -> FetchedContent:
        assert_url_is_safe(url)

        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text[: self._max_bytes]
            final_url = str(response.url)

        # Re-chequear la URL final tras redirects
        try:
            assert_url_is_safe(final_url)
        except SSRFBlocked as e:
            raise SSRFBlocked(f"Redirect inseguro: {e}") from e

        # Extraer texto canónico
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_recall=False,
            no_fallback=False,
        ) or ""

        # Metadata
        metadata = trafilatura.extract_metadata(html)
        title = metadata.title if metadata else None
        published_at = None
        if metadata and metadata.date:
            try:
                published_at = datetime.fromisoformat(metadata.date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                published_at = None

        # Detección de idioma
        language: str | None = None
        if extracted:
            try:
                language = detect(extracted[:2000])
            except LangDetectException:
                language = None

        return FetchedContent(
            canonical_url=final_url,
            title=title,
            text=extracted,
            published_at=published_at,
            language=language,
            raw_html=None,  # no guardamos HTML por defecto (memoria)
            is_paywalled=len(extracted) < 200 and len(html) > 5000,
            fetched_at=datetime.now(UTC),
        )
