from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

from app.webapi.routes import router as api_router
from app.core.settings import get_settings
from app.core.db import init_db
from app.core.logging import setup_logging
from starlette.middleware.sessions import SessionMiddleware

# Configure logging immediately
setup_logging()


def create_app() -> FastAPI:
    settings = get_settings()
    allow_origins = [settings.frontend_origin] if settings.frontend_origin else ["*"]
    app = FastAPI(title="CONTEXTOR (TEAM) API", version="0.1.0")
    
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],  # 개발 편의
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------
    # Routers
    # -------------------------
    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()

    logger = logging.getLogger("app.request")

    @app.middleware("http")
    async def log_requests(request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    # -------------------------
    # Health check
    # -------------------------
    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
