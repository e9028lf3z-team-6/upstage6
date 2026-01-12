from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.webapi.routes import router as api_router
from app.core.settings import get_settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # -------------------------
    # Startup
    # -------------------------
    load_dotenv()
    await init_db()
    yield
    # -------------------------
    # Shutdown (필요 시 확장)
    # -------------------------


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="CONTEXTOR (TEAM) API",
        version="0.1.0",
        description="LangGraph 기반 문서 분석 및 리라이트 에이전트 API",
        lifespan=lifespan,
    )

    # -------------------------
    # CORS
    # -------------------------
    allow_origins = []
    if settings.frontend_origin:
        if isinstance(settings.frontend_origin, str):
            allow_origins = [o.strip() for o in settings.frontend_origin.split(",")]
        else:
            allow_origins = settings.frontend_origin

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

    # -------------------------
    # Health check
    # -------------------------
    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
