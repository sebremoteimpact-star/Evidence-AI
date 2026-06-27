"""Schemas Pydantic para autenticación."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128, description="Mínimo 10 caracteres")
    name: str | None = Field(default=None, max_length=255)
    locale: str = Field(default="es", pattern="^(es|en)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    access_expires_at: datetime
    refresh_expires_at: datetime


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None
    locale: str
    is_admin: bool
    created_at: datetime


class RegisterResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
