"""Manejador centralizado de errores — formato RFC 7807 Problem Details."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from evidence_ai.application.use_cases.authenticate_user import (
    InactiveUserError,
    InvalidCredentialsError,
)
from evidence_ai.application.use_cases.create_verification import (
    InputTooLargeError,
    InvalidInputError,
)
from evidence_ai.application.use_cases.register_user import (
    UserAlreadyExistsError,
    WeakPasswordError,
)

logger = structlog.get_logger(__name__)


def _problem(
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url),
    }
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status_code, content=body, media_type="application/problem+json")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return _problem(
            request,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Solicitud inválida",
            "Uno o más campos no superan validación. Revisa 'errors'.",
            type_="https://evidence-ai/errors/validation",
            extra={"errors": exc.errors()},
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
        return _problem(
            request,
            status.HTTP_409_CONFLICT,
            "Usuario ya existe",
            str(exc),
            type_="https://evidence-ai/errors/user-exists",
        )

    @app.exception_handler(WeakPasswordError)
    async def weak_password_handler(request: Request, exc: WeakPasswordError):
        return _problem(
            request,
            status.HTTP_400_BAD_REQUEST,
            "Contraseña débil",
            str(exc),
            type_="https://evidence-ai/errors/weak-password",
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
        return _problem(
            request,
            status.HTTP_401_UNAUTHORIZED,
            "Credenciales inválidas",
            str(exc),
            type_="https://evidence-ai/errors/invalid-credentials",
        )

    @app.exception_handler(InactiveUserError)
    async def inactive_user_handler(request: Request, exc: InactiveUserError):
        return _problem(
            request,
            status.HTTP_403_FORBIDDEN,
            "Cuenta desactivada",
            str(exc),
            type_="https://evidence-ai/errors/inactive-user",
        )

    @app.exception_handler(InputTooLargeError)
    async def input_too_large_handler(request: Request, exc: InputTooLargeError):
        return _problem(
            request,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "Input demasiado grande",
            str(exc),
            type_="https://evidence-ai/errors/input-too-large",
        )

    @app.exception_handler(InvalidInputError)
    async def invalid_input_handler(request: Request, exc: InvalidInputError):
        return _problem(
            request,
            status.HTTP_400_BAD_REQUEST,
            "Input inválido",
            str(exc),
            type_="https://evidence-ai/errors/invalid-input",
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_handler(request: Request, exc: SQLAlchemyError):
        logger.error("db_error", error=str(exc), exc_info=True)
        return _problem(
            request,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Error de base de datos",
            "El servicio no pudo completar la operación. Intenta de nuevo.",
            type_="https://evidence-ai/errors/db-unavailable",
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("unhandled_error", error=str(exc))
        return _problem(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error interno del servidor",
            "Ocurrió un error inesperado. El equipo ha sido notificado.",
            type_="https://evidence-ai/errors/internal",
        )
