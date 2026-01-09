from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
os.getenv("UPSTAGE_API_KEY")


from fastapi import FastAPI
from app.api.agent import router as agent_router

app = FastAPI(title="Agentic Eval")
app.include_router(agent_router)
