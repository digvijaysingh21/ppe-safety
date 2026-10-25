"""Structured logging.

Why structured: logs become key-value events (`camera_id=cam-03 event=...`)
that tools like Loki can filter, instead of free text you must grep.
Locally we render them readable; in production (`log_json=True`) as JSON.
"""

from __future__ import annotations

import logging

import structlog
from structlog.typing import FilteringBoundLogger


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Call once at process start (service main or script entry)."""
    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    logger: FilteringBoundLogger = structlog.get_logger(name)
    return logger
