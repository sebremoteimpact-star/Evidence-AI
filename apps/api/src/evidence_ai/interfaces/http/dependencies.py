"""Dependencias FastAPI — extracción del usuario autenticado del JWT.

Modo invitado: si no hay token, todas las peticiones se atribuyen a un
usuario "demo" compartido. Útil para demos y para evitar fricción de
registro. El usuario demo se auto-crea en el lifespan del API.
"""

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

# Usuario demo compartido — se usa cuando no hay JWT
GUEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
GUEST_USER_EMAIL = "guest@evidence-ai.local"


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
    """Extrae el user_id del header Authorization: Bearer ...
    Si no hay token, devuelve el GUEST_USER_ID (modo invitado).
    """
    if credentials is None:
        return GUEST_USER_ID
    try:
        return _verify_token(credentials.credentials, jwt_service)
    except HTTPException:
        # Token inválido → fallback a invitado (demo-friendly)
        return GUEST_USER_ID


@inject
async def get_current_user_id_sse(
    token: Annotated[str | None, Query(description="Token JWT (opcional)")] = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
) -> UUID:
    """Variante para SSE. Si no hay token, modo invitado."""
    raw = credentials.credentials if credentials else token
    if not raw:
        return GUEST_USER_ID
    try:
        return _verify_token(raw, jwt_service)
    except HTTPException:
        return GUEST_USER_ID


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
CurrentUserIdSse = Annotated[UUID, Depends(get_current_user_id_sse)]
