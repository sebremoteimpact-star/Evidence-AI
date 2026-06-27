"""Dependencias FastAPI — extracción del usuario autenticado del JWT."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from evidence_ai.config.container import Container
from evidence_ai.infrastructure.auth.jwt_service import JwtService

bearer_scheme = HTTPBearer(auto_error=False)


@inject
async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    jwt_service: Annotated[JwtService, Depends(Provide[Container.jwt_service])],
) -> UUID:
    """Extrae el user_id del JWT del header Authorization. Lanza 401 si falla."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta token de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt_service.verify(credentials.credentials, expected_type="access")
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


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
