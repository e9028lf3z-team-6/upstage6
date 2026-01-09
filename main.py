from pathlib import Path
from dotenv import load_dotenv
import os

from fastapi import FastAPI

# -----------------------------
# 환경 변수 로드
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

os.getenv("UPSTAGE_API_KEY")


# -----------------------------
# Router import
# -----------------------------
from app.api.router import router as tools_router
from app.api.develope_route import router as dev_router


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="Agentic Eval")

# 운영용 Agent 파이프라인
app.include_router(tools_router)

# 개발 / metrics / 실험용 API
app.include_router(dev_router)
