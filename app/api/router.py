from fastapi import APIRouter
from app.schemas.agent import AgentRequest
from app.services.pipeline_runner import run_full_pipeline

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/run")
def run_agent(req: AgentRequest):
    return run_full_pipeline(req.text)
