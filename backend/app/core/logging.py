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


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        
        # [PROGRESS] 태그가 있는 경우 별도 표시 (예: 색상 코드 추가 가능하나 여기선 단순화)
        message = record.getMessage()
        if "[PROGRESS]" in message:
            message = f"🚀 {message}"
            
        return f"[{timestamp}] [{record.levelname:<5}] [{record.name}] {message}"


def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "text").lower()  # Default to text for local dev
    formatter = "json" if log_format == "json" else "text"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": JsonFormatter},
            "text": {"()": TextFormatter},
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "root": {"handlers": ["default"], "level": level},
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
            # Reduce noise from external libraries
            "httpx": {"handlers": ["default"], "level": "WARNING", "propagate": False},
            "httpcore": {"handlers": ["default"], "level": "WARNING", "propagate": False},
            "openai": {"handlers": ["default"], "level": "WARNING", "propagate": False},
        },
    })
