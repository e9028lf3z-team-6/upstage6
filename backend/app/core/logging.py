import json
import logging
import logging.config
import os
import time
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        standard = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process",
        }
        for key, value in record.__dict__.items():
            if key in standard or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json").lower()
    formatter = "json" if log_format == "json" else "console"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": JsonFormatter},
            "console": {"format": "%(levelname)s %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
            },
        },
        "root": {"handlers": ["default"], "level": level},
    })
