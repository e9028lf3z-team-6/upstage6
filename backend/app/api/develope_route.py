from fastapi import APIRouter
from app.schemas.agent import AgentRequest
from app.services.pipeline_runner import run_full_pipeline
from app.langgraph.graph import run_langgraph_pipeline

router = APIRouter(prefix="/dev", tags=["dev-metric"])


@router.post("/metric/run")
def run_metric_dev(req: AgentRequest, use_langgraph: bool = False):
    """
    Metric 개발/디버깅 전용
    - 서비스 파이프라인 100% 재사용
    """

    if use_langgraph:
        result = run_langgraph_pipeline(req.text, debug=True)
    else:
        result = run_full_pipeline(req.text, debug=True)

    return {
        "input": req.text,
        "issue_count": {
            "tone": len(result["tone"].get("issues", [])),
            "causality": len(result["causality"].get("issues", [])),
            "trauma": len(result.get("trauma", {}).get("issues", [])),
            "hate_bias": len(result.get("hate_bias", {}).get("issues", [])),
            "genre_cliche": len(result.get("genre_cliche", {}).get("issues", [])),
        },
        "final_metric": result.get("final_metric"),
        "debug": result.get("debug"),
    }
