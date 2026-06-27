"""Proveedor de búsqueda DuckDuckGo — gratis, sin API key."""

from __future__ import annotations

import asyncio

import structlog
from duckduckgo_search import DDGS

from evidence_ai.application.ports.search_provider import (
    SearchProvider,
    SearchQuery,
    SearchResult,
)

logger = structlog.get_logger(__name__)


class DuckDuckGoProvider:
    name = "duckduckgo"

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        text = query.text
        if query.site:
            text = f"{text} site:{query.site}"

        # DDGS es sync — ejecutamos en executor para no bloquear el event loop
        def _do_search() -> list[dict]:
            try:
                with DDGS() as ddgs:
                    return list(
                        ddgs.text(
                            text,
                            region="wt-wt",
                            safesearch="moderate",
                            timelimit=None,
                            max_results=query.max_results,
                        )
                    )
            except Exception as e:
                logger.warning("ddg_search_failed", error=str(e), query=text)
                return []

        raw = await asyncio.get_event_loop().run_in_executor(None, _do_search)
        return [
            SearchResult(
                url=item.get("href", ""),
                title=item.get("title", ""),
                snippet=item.get("body", ""),
                provider=self.name,
            )
            for item in raw
            if item.get("href")
        ]

    async def is_available(self) -> bool:
        return True  # No requiere credenciales
