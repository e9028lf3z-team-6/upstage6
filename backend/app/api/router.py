from fastapi import APIRouter
from backend.app.schemas.agent import AgentRequest
from backend.app.services.pipeline_runner import run_full_pipeline

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/run")
def run_agent(req: AgentRequest):
    return run_full_pipeline(req.text)
