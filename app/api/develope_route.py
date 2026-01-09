from fastapi import APIRouter
from app.schemas.agent import AgentRequest
from app.services.pipeline_runner import run_full_pipeline

router = APIRouter(prefix="/dev", tags=["dev-metric"])


@router.post("/metric/run")
def run_metric_dev(req: AgentRequest):
    """
    Metric 개발/디버깅 전용
    - 서비스 파이프라인 100% 재사용
    """

    result = run_full_pipeline(req.text, debug=True)

    return {
        "input": req.text,
        "issue_count": {
            "tone": len(result["tone"].get("issues", [])),
            "causality": len(result["causality"].get("issues", [])),
            "trauma": len(result["trauma"].get("issues", [])),
            "hate_bias": len(result["hate_bias"].get("issues", [])),
            "genre_cliche": len(result["genre_cliche"].get("issues", [])),
        },
        "final_metric": result["final_metric"],
        "debug": result["debug"],
    }
