"""Container DI — wiring de toda la aplicación.

Una sola fuente de verdad de cómo se construyen los componentes.
Los tests pueden sobrescribir cualquier provider con `.override(...)`.
"""

from __future__ import annotations

from dependency_injector import containers, providers
from redis.asyncio import Redis

from evidence_ai.application.use_cases.authenticate_user import AuthenticateUserUseCase
from evidence_ai.application.use_cases.create_verification import CreateVerificationUseCase
from evidence_ai.application.use_cases.register_user import RegisterUserUseCase
from evidence_ai.application.use_cases.verify_content import VerifyContentUseCase
from evidence_ai.config.settings import Settings, get_settings
from evidence_ai.domain.services.confidence_calculator import ConfidenceCalculator
from evidence_ai.infrastructure.ai.claude_reasoner import ClaudeAIReasoner
from evidence_ai.infrastructure.auth.jwt_service import JwtService
from evidence_ai.infrastructure.auth.password_hasher import Argon2PasswordHasher
from evidence_ai.infrastructure.cache.redis_cache import RedisCache
from evidence_ai.infrastructure.events.inprocess_job_queue import InProcessJobQueue
from evidence_ai.infrastructure.events.redis_event_publisher import RedisEventPublisher
from evidence_ai.infrastructure.fetchers.readability_fetcher import ReadabilityFetcher
from evidence_ai.infrastructure.fetchers.youtube_fetcher import YouTubeTranscriptFetcher
from evidence_ai.infrastructure.persistence.database import (
    create_engine,
    create_session_factory,
)
from evidence_ai.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)
from evidence_ai.infrastructure.persistence.repositories.sql_verification_repository import (
    SqlVerificationRepository,
)
from evidence_ai.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from evidence_ai.infrastructure.search.duckduckgo_provider import DuckDuckGoProvider


async def _create_redis(url: str) -> Redis:
    return Redis.from_url(url, decode_responses=False)


class Container(containers.DeclarativeContainer):
    """Container raíz. Compartido entre API y Worker."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "evidence_ai.interfaces.http.routers.health",
            "evidence_ai.interfaces.http.routers.auth",
            "evidence_ai.interfaces.http.routers.verifications",
            "evidence_ai.interfaces.http.routers.stream",
            "evidence_ai.interfaces.http.dependencies",
        ]
    )

    # ─── Config ───
    settings: providers.Singleton[Settings] = providers.Singleton(get_settings)

    # ─── Datos ───
    engine = providers.Singleton(create_engine, settings=settings)
    session_factory = providers.Singleton(create_session_factory, engine=engine)

    # ─── Redis ───
    redis = providers.Resource(_create_redis, url=settings.provided.redis_url)

    # ─── UoW + Repositorios (Factory: una instancia por request/use case) ───
    unit_of_work = providers.Factory(
        SqlAlchemyUnitOfWork, session_factory=session_factory
    )
    user_repository_factory = providers.Object(lambda uow: SqlUserRepository(uow))
    verification_repository_factory = providers.Object(
        lambda uow: SqlVerificationRepository(uow)
    )

    # ─── Servicios de infraestructura ───
    password_hasher = providers.Singleton(Argon2PasswordHasher)
    jwt_service = providers.Singleton(JwtService, settings=settings)
    cache = providers.Singleton(RedisCache, redis=redis)
    event_publisher = providers.Singleton(
        RedisEventPublisher, redis=redis, session_factory=session_factory
    )

    # ─── Componentes del pipeline ───
    duckduckgo_provider = providers.Singleton(DuckDuckGoProvider)
    youtube_fetcher = providers.Singleton(YouTubeTranscriptFetcher)
    readability_fetcher = providers.Singleton(ReadabilityFetcher)
    ai_reasoner = providers.Singleton(ClaudeAIReasoner, settings=settings)
    confidence_calculator = providers.Singleton(ConfidenceCalculator)

    # Use case del pipeline (factory para que cada job tenga su instancia)
    verify_content_use_case = providers.Factory(
        VerifyContentUseCase,
        uow_factory=unit_of_work.provider,
        fetchers=providers.List(youtube_fetcher, readability_fetcher),
        search_providers=providers.List(duckduckgo_provider),
        ai_reasoner=ai_reasoner,
        event_publisher=event_publisher,
        confidence_calculator=confidence_calculator,
        max_sources_per_claim=settings.provided.max_sources_per_claim,
    )

    # ─── Job queue (in-process — sin worker separado) ───
    job_queue = providers.Singleton(
        InProcessJobQueue,
        use_case_provider=verify_content_use_case.provider,
    )

    # ─── Casos de uso públicos ───
    register_user_use_case = providers.Factory(
        RegisterUserUseCase,
        uow=unit_of_work,
        user_repo_factory=user_repository_factory,
        password_hasher=password_hasher,
    )
    authenticate_user_use_case = providers.Factory(
        AuthenticateUserUseCase,
        uow=unit_of_work,
        user_repo_factory=user_repository_factory,
        password_hasher=password_hasher,
    )
    create_verification_use_case = providers.Factory(
        CreateVerificationUseCase,
        uow=unit_of_work,
        verification_repo_factory=verification_repository_factory,
        job_queue=job_queue,
        max_input_chars=settings.provided.max_input_chars,
    )
