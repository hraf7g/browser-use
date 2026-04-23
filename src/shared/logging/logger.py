from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.shared.config.settings import Settings, get_settings

_RESERVED_LOG_RECORD_ATTRS = {
    'args',
    'asctime',
    'created',
    'exc_info',
    'exc_text',
    'filename',
    'funcName',
    'levelname',
    'levelno',
    'lineno',
    'module',
    'msecs',
    'message',
    'msg',
    'name',
    'pathname',
    'process',
    'processName',
    'relativeCreated',
    'stack_info',
    'thread',
    'threadName',
    'taskName',
}


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter for structured application logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_ATTRS or key.startswith('_'):
                continue
            payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


def setup_logging(settings: Settings | None = None) -> None:
    """Configure root logging once in an idempotent way."""
    cfg = settings or get_settings()
    root_logger = logging.getLogger()

    if getattr(root_logger, "_utw_logging_configured", False):
        return

    root_logger.setLevel(cfg.log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Keep third-party logs readable but quieter.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    setattr(root_logger, "_utw_logging_configured", True)


def get_logger(name: str) -> logging.Logger:
    """Return a standard logger for the given module."""
    return logging.getLogger(name)
