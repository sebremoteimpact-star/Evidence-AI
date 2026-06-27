"""Entidad User — usuario del sistema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    id: UUID
    email: str
    name: str | None
    password_hash: str | None
    """None si el usuario solo se autentica vía OAuth."""

    oauth_provider: str | None
    """'google' u otro proveedor; None si solo email/password."""

    oauth_subject: str | None
    """Subject ID estable del proveedor OAuth."""

    locale: str
    """Código ISO 639-1: 'es' | 'en'."""

    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
