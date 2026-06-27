"""Configuración de logging estructurado con structlog."""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """Configura logging estructurado para toda la app.

    Args:
        level: nivel mínimo de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_logs: True en producción (JSON), False en dev (color, legible).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configurar stdlib logging para que las libs externas también vayan a stdout
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    # Procesadores NATIVOS de structlog (no stdlib — esos requieren un logger
    # con .name y .level que PrintLogger no tiene → AttributeError en runtime)
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,  # structlog-native, no stdlib
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    renderer = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Silenciar librerías ruidosas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str = "") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
