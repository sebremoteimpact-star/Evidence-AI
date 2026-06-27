"""Carga plantillas de prompts desde archivos .md."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Carga el contenido de un prompt por nombre (sin .md).

    Ej: load_prompt('extract_claims') → str con el contenido del archivo.
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt no encontrado: {path}")
    return path.read_text(encoding="utf-8")


def render(template: str, **kwargs) -> str:
    """Render simple por reemplazo de {placeholder} → valor."""
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template
