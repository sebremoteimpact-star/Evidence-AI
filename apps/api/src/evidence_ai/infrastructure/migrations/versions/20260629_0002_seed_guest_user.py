"""Seed del usuario invitado para modo demo.

Revision ID: 20260629_0002
Revises: 20260626_0001
Create Date: 2026-06-29 12:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260629_0002"
down_revision: str | Sequence[str] | None = "20260626_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


GUEST_USER_ID = "00000000-0000-0000-0000-000000000001"
GUEST_USER_EMAIL = "guest@evidence-ai.local"


def upgrade() -> None:
    """Crea el usuario invitado si no existe. Idempotente."""
    op.execute(
        f"""
        INSERT INTO users (id, email, name, password_hash, oauth_provider, oauth_subject,
                           locale, is_active, is_admin, created_at, updated_at)
        VALUES (
            '{GUEST_USER_ID}',
            '{GUEST_USER_EMAIL}',
            'Invitado',
            NULL, NULL, NULL,
            'es', true, false,
            NOW(), NOW()
        )
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM users WHERE id = '{GUEST_USER_ID}';")
