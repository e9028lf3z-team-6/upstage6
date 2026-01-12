from fastapi import APIRouter
from app.schemas.agent import AgentRequest
from app.services.pipeline_runner import run_full_pipeline
from app.langgraph.graph import run_langgraph_pipeline

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/run")
def run_agent(req: AgentRequest, use_langgraph: bool = False):
    if use_langgraph:
        return run_langgraph_pipeline(req.text, debug=True)
    return run_full_pipeline(req.text)
