"""Configuración centralizada — Pydantic Settings.

Lee todas las variables de entorno con validación tipada.
Una sola fuente de verdad para configuración. Acceso vía `get_settings()`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Configuración global de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Entorno ──
    environment: Environment = "development"
    log_level: str = "INFO"

    # ── Datos ──
    database_url: str = Field(
        default="postgresql+asyncpg://evidence:cambiar_en_local@localhost:5432/evidence_ai",
        description="DSN async para SQLAlchemy (postgresql+asyncpg://...)",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="DSN para Redis (cache + cola arq + pubsub)",
    )

    # ── IA ──
    anthropic_api_key: SecretStr = SecretStr("")
    claude_reasoning_model: str = "claude-sonnet-4-6"
    claude_fast_model: str = "claude-haiku-4-5-20251001"
    claude_max_tokens: int = 4096

    # ── Búsqueda ──
    search_providers: str = "duckduckgo,brave,google_cse"
    brave_search_api_key: SecretStr = SecretStr("")
    google_cse_api_key: SecretStr = SecretStr("")
    google_cse_id: str = ""

    # ── Auth ──
    jwt_secret: SecretStr = SecretStr("cambiar_a_random_seguro_minimo_32_chars")
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    google_oauth_client_id: str = ""
    google_oauth_client_secret: SecretStr = SecretStr("")

    # ── HTTP ──
    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str = ""
    """Regex opcional para orígenes — útil para previews de Vercel (*.vercel.app).
    Ejemplo: 'https://.*\\.vercel\\.app'."""

    # ── Rate limits ──
    rate_limit_default: str = "60/minute"
    rate_limit_verification: str = "10/hour"

    # ── Límites del pipeline ──
    max_claims_per_verification: int = 15
    max_sources_per_claim: int = 12
    max_input_chars: int = 50_000
    verification_timeout_seconds: int = 180

    # ── Archivos ──
    upload_dir: Path = Path("/app/data/uploads")
    max_upload_size_mb: int = 500

    # ── Observabilidad ──
    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "evidence-ai-api"

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: SecretStr) -> SecretStr:
        secret = v.get_secret_value()
        if len(secret) < 32:
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def search_providers_list(self) -> list[str]:
        return [p.strip() for p in self.search_providers.split(",") if p.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    """Singleton de settings. lru_cache para reusar la instancia."""
    return Settings()
