"""Fetcher de transcripts de YouTube."""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import structlog
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from evidence_ai.application.ports.content_fetcher import FetchedContent

logger = structlog.get_logger(__name__)

_YOUTUBE_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})")


def extract_video_id(url: str) -> str | None:
    """Extrae el video ID de cualquier formato de URL de YouTube."""
    if "youtu.be/" in url:
        path = urlparse(url).path
        return path.lstrip("/").split("/")[0] or None
    if "youtube.com/watch" in url:
        qs = parse_qs(urlparse(url).query)
        v = qs.get("v")
        return v[0] if v else None
    match = _YOUTUBE_RE.search(url)
    return match.group(1) if match else None


class YouTubeTranscriptFetcher:
    async def can_handle(self, url: str) -> bool:
        return extract_video_id(url) is not None

    async def fetch(self, url: str) -> FetchedContent:
        video_id = extract_video_id(url)
        if video_id is None:
            raise ValueError(f"No se pudo extraer video ID de: {url}")

        def _fetch_transcript() -> tuple[str, str | None]:
            try:
                # Intenta múltiples idiomas, priorizando los más comunes
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["es", "en", "pt", "fr", "de"]
                )
                text = " ".join(item["text"] for item in transcript)
                return text, None  # idioma se detecta después
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                raise ValueError(
                    "Este video no tiene subtítulos disponibles. "
                    "Sube manualmente el transcript si lo tienes."
                ) from e

        text, _ = await asyncio.get_event_loop().run_in_executor(None, _fetch_transcript)

        return FetchedContent(
            canonical_url=f"https://www.youtube.com/watch?v={video_id}",
            title=None,
            text=text,
            published_at=None,
            language=None,
            raw_html=None,
            is_paywalled=False,
            fetched_at=datetime.now(UTC),
        )
