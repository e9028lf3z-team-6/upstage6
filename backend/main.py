import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.webapi.routes import router as api_router
from app.core.settings import get_settings
from app.core.db import init_db
from dotenv import load_dotenv

load_dotenv()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CONTEXTOR (TEAM) API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup():
        await init_db()

    app.include_router(api_router, prefix="/api")
    return app

app = create_app()
