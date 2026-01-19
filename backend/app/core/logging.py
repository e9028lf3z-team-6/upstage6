import logging
import logging.config
import os
from typing import Any

class SimpleFormatter(logging.Formatter):
    """메타데이터 없이 메시지만 출력하는 포맷터 (색상 지원)"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        
        # [START]가 포함되면 초록색, [END]가 포함되면 빨간색 적용
        if "[START]" in msg:
            msg = f"{self.GREEN}{msg}{self.RESET}"
        elif "[END]" in msg:
            msg = f"{self.RED}{msg}{self.RESET}"
        
        return msg

class NoDebugFilter(logging.Filter):
    """[DEBUG]가 포함된 로그는 차단"""
    def filter(self, record: logging.LogRecord) -> bool:
        return "[DEBUG]" not in record.getMessage()

def setup_logging() -> None:
    # 모든 외부 라이브러리 로그를 차단하고 app 로그만 간단히 표시
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "no_debug": {
                "()": NoDebugFilter
            }
        },
        "formatters": {
            "simple": {"()": SimpleFormatter},
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "filters": ["no_debug"],
            },
        },
        "loggers": {
            "root": {"handlers": ["default"], "level": "WARNING"},
            "app": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn": {"handlers": ["default"], "level": "WARNING"},
            "uvicorn.access": {"handlers": ["default"], "level": "WARNING"},
            "httpcore": {"handlers": ["default"], "level": "WARNING"},
            "httpx": {"handlers": ["default"], "level": "WARNING"},
        }
    })
