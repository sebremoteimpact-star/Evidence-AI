"""Base declarativa de SQLAlchemy y mixins comunes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import UUID, DateTime, MetaData, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ─────────────────────────────────────────────
# Naming convention — migraciones reproducibles
# ─────────────────────────────────────────────
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ─────────────────────────────────────────────
# Tipos anotados reutilizables (SQLAlchemy 2.0 style)
# ─────────────────────────────────────────────

UuidPk = Annotated[
    uuid.UUID,
    mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
]

TimestampTz = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now()),
]


class TimestampMixin:
    """Mixin con created_at + updated_at gestionados por la DB."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
