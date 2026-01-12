# app/api/tools_router.py
from fastapi import APIRouter
from app.schemas.agent import AgentRequest
from app.services.pipeline_runner import run_full_pipeline

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/run")
def run_agent(req: AgentRequest):
    """
    프로덕션용 에이전트 실행 API
    - LangGraph 기반 전체 파이프라인 실행
    - 사용자에게 필요한 결과만 반환
    """

    result = run_full_pipeline(
        text=req.text,
        expected=req.expected,
        debug=False,
    )

    return {
        "decision": result.get("decision"),
        "report": result.get("final_report"),
    }
