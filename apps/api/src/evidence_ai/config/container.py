"""Container DI — wiring de toda la aplicación.

Una sola fuente de verdad de cómo se construyen los componentes.
Los tests pueden sobrescribir cualquier provider con `.override(...)`.
"""

from __future__ import annotations

from arq import create_pool
from arq.connections import RedisSettings
from dependency_injector import containers, providers
from redis.asyncio import Redis

from evidence_ai.application.use_cases.authenticate_user import AuthenticateUserUseCase
from evidence_ai.application.use_cases.create_verification import CreateVerificationUseCase
from evidence_ai.application.use_cases.register_user import RegisterUserUseCase
from evidence_ai.config.settings import Settings, get_settings
from evidence_ai.infrastructure.auth.jwt_service import JwtService
from evidence_ai.infrastructure.auth.password_hasher import Argon2PasswordHasher
from evidence_ai.infrastructure.cache.redis_cache import RedisCache
from evidence_ai.infrastructure.events.arq_job_queue import ArqJobQueue
from evidence_ai.infrastructure.events.redis_event_publisher import RedisEventPublisher
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


async def _create_redis(url: str) -> Redis:
    return Redis.from_url(url, decode_responses=False)


async def _create_arq_pool(url: str):
    return await create_pool(RedisSettings.from_dsn(url))


class Container(containers.DeclarativeContainer):
    """Container raíz. Compartido entre API y Worker."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "evidence_ai.interfaces.http.routers.health",
            "evidence_ai.interfaces.http.routers.auth",
            "evidence_ai.interfaces.http.routers.verifications",
        ]
    )

    # ─── Config ───
    settings: providers.Singleton[Settings] = providers.Singleton(get_settings)

    # ─── Datos ───
    engine = providers.Singleton(create_engine, settings=settings)
    session_factory = providers.Singleton(create_session_factory, engine=engine)

    # ─── Redis ───
    redis = providers.Resource(_create_redis, url=settings.provided.redis_url)
    arq_pool = providers.Resource(_create_arq_pool, url=settings.provided.redis_url)

    # ─── UoW + Repositorios (Factory: una instancia por request/use case) ───
    unit_of_work = providers.Factory(
        SqlAlchemyUnitOfWork, session_factory=session_factory
    )
    user_repository_factory = providers.Object(
        lambda uow: SqlUserRepository(uow)
    )
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
    job_queue = providers.Singleton(ArqJobQueue, redis=arq_pool)

    # ─── Casos de uso ───
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
