"""Mapper User ↔ UserModel."""

from __future__ import annotations

from evidence_ai.domain.entities import User
from evidence_ai.infrastructure.persistence.models import UserModel


def model_to_user(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        name=model.name,
        password_hash=model.password_hash,
        oauth_provider=model.oauth_provider,
        oauth_subject=model.oauth_subject,
        locale=model.locale,
        is_active=model.is_active,
        is_admin=model.is_admin,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id,
        email=entity.email,
        name=entity.name,
        password_hash=entity.password_hash,
        oauth_provider=entity.oauth_provider,
        oauth_subject=entity.oauth_subject,
        locale=entity.locale,
        is_active=entity.is_active,
        is_admin=entity.is_admin,
    )
