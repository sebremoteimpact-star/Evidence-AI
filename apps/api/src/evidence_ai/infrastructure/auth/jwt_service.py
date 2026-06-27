"""Emisión y verificación de JWTs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from evidence_ai.config.settings import Settings


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


@dataclass(frozen=True)
class TokenPayload:
    sub: UUID  # user id
    email: str
    is_admin: bool
    token_type: str  # "access" | "refresh"
    exp: int
    iat: int
    jti: str


class JwtService:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret.get_secret_value()
        self._algorithm = settings.jwt_algorithm
        self._access_ttl = timedelta(minutes=settings.jwt_access_ttl_minutes)
        self._refresh_ttl = timedelta(days=settings.jwt_refresh_ttl_days)

    def issue(self, user_id: UUID, email: str, is_admin: bool) -> TokenPair:
        now = datetime.now(UTC)
        access_exp = now + self._access_ttl
        refresh_exp = now + self._refresh_ttl

        access_jti = f"a:{user_id}:{int(now.timestamp())}"
        refresh_jti = f"r:{user_id}:{int(now.timestamp())}"

        access = jwt.encode(
            {
                "sub": str(user_id),
                "email": email,
                "is_admin": is_admin,
                "token_type": "access",
                "exp": int(access_exp.timestamp()),
                "iat": int(now.timestamp()),
                "jti": access_jti,
            },
            self._secret,
            algorithm=self._algorithm,
        )
        refresh = jwt.encode(
            {
                "sub": str(user_id),
                "email": email,
                "is_admin": is_admin,
                "token_type": "refresh",
                "exp": int(refresh_exp.timestamp()),
                "iat": int(now.timestamp()),
                "jti": refresh_jti,
            },
            self._secret,
            algorithm=self._algorithm,
        )
        return TokenPair(access, refresh, access_exp, refresh_exp)

    def verify(self, token: str, expected_type: str = "access") -> TokenPayload:
        """Verifica el token. Lanza jwt.PyJWTError en caso de error."""
        decoded = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        if decoded.get("token_type") != expected_type:
            raise jwt.InvalidTokenError(
                f"Tipo de token incorrecto: esperado {expected_type}, recibido {decoded.get('token_type')}"
            )
        return TokenPayload(
            sub=UUID(decoded["sub"]),
            email=decoded["email"],
            is_admin=decoded.get("is_admin", False),
            token_type=decoded["token_type"],
            exp=decoded["exp"],
            iat=decoded["iat"],
            jti=decoded["jti"],
        )
