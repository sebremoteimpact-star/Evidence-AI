"""Endpoints de autenticación: registro, login, refresh."""

from __future__ import annotations

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from evidence_ai.application.use_cases.authenticate_user import (
    AuthenticateUserCommand,
    AuthenticateUserUseCase,
)
from evidence_ai.application.use_cases.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from evidence_ai.config.container import Container
from evidence_ai.infrastructure.auth.jwt_service import JwtService
from evidence_ai.interfaces.http.schemas.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
@inject
async def register(
    body: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(Provide[Container.register_user_use_case]),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
) -> RegisterResponse:
    user = await use_case.execute(
        RegisterUserCommand(
            email=body.email,
            password=body.password,
            name=body.name,
            locale=body.locale,
        )
    )
    tokens = jwt_service.issue(user.id, user.email, user.is_admin)
    return RegisterResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            locale=user.locale,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ),
        tokens=TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            access_expires_at=tokens.access_expires_at,
            refresh_expires_at=tokens.refresh_expires_at,
        ),
    )


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
@inject
async def login(
    body: LoginRequest,
    use_case: AuthenticateUserUseCase = Depends(Provide[Container.authenticate_user_use_case]),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
) -> TokenResponse:
    user = await use_case.execute(
        AuthenticateUserCommand(email=body.email, password=body.password)
    )
    tokens = jwt_service.issue(user.id, user.email, user.is_admin)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        access_expires_at=tokens.access_expires_at,
        refresh_expires_at=tokens.refresh_expires_at,
    )
