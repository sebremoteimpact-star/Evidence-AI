"""Mapeo dominio → (tier, type) leído del JSON compartido."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from evidence_ai.domain.value_objects.source_tier import SourceTier
from evidence_ai.domain.value_objects.source_type import SourceType

# Ruta relativa al raíz del repo
_REGISTRY_PATH = (
    Path(__file__).resolve().parents[5] / "packages" / "source-registry" / "registry.json"
)


@lru_cache(maxsize=1)
def _load_raw() -> dict:
    return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))


def extract_domain(url: str) -> str:
    """Devuelve el dominio sin www. (ej: 'www.who.int' → 'who.int')."""
    netloc = urlparse(url).netloc.lower()
    return netloc.removeprefix("www.")


def lookup(url: str) -> tuple[SourceTier, SourceType, str | None]:
    """Devuelve (tier, type, notes) para una URL.

    Si el dominio no está en el registry, asume tier 6 (periodismo/desconocido).
    Si está en blocked_as_primary, devuelve tier 6 con nota.
    """
    raw = _load_raw()
    domain = extract_domain(url)

    if domain in raw.get("blocked_as_primary", []):
        return (SourceTier.JOURNALISM, SourceType.OTHER,
                f"{domain} no se acepta como fuente primaria; se trata solo como referencia.")

    entry = raw.get("domains", {}).get(domain)
    if entry is None:
        # Buscar superdominio (ej: subdominio.who.int → who.int)
        for d, info in raw.get("domains", {}).items():
            if domain.endswith("." + d):
                entry = info
                break

    if entry is None:
        return (SourceTier.JOURNALISM, SourceType.OTHER, None)

    tier = SourceTier(int(entry["tier"]))
    source_type = SourceType(entry["type"])
    notes = entry.get("notes")
    return tier, source_type, notes


def all_tier_info() -> dict:
    return _load_raw().get("tiers", {})
