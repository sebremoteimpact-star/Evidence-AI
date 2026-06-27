"""Dependencias FastAPI — extracción del usuario autenticado del JWT."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from evidence_ai.config.container import Container
from evidence_ai.infrastructure.auth.jwt_service import JwtService

bearer_scheme = HTTPBearer(auto_error=False)


def _verify_token(token: str, jwt_service: JwtService) -> UUID:
    try:
        payload = jwt_service.verify(token, expected_type="access")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from None
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from None
    return payload.sub


@inject
async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    jwt_service: Annotated[JwtService, Depends(Provide[Container.jwt_service])],
) -> UUID:
    """Extrae el user_id del header Authorization: Bearer ..."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta token de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _verify_token(credentials.credentials, jwt_service)


@inject
async def get_current_user_id_sse(
    token: Annotated[str | None, Query(description="Token JWT (necesario para SSE)")] = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
) -> UUID:
    """Variante para SSE — EventSource del navegador no soporta headers custom,
    así que aceptamos ?token=... como fallback. El token va por HTTPS.
    """
    raw = credentials.credentials if credentials else token
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta token (header Authorization o ?token=...)",
        )
    return _verify_token(raw, jwt_service)


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
CurrentUserIdSse = Annotated[UUID, Depends(get_current_user_id_sse)]
