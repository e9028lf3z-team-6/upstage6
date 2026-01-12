# app/api/dev_metric_router.py
from fastapi import APIRouter
from app.schemas.agent import AgentRequest
from app.services.pipeline_runner import run_full_pipeline

router = APIRouter(prefix="/dev", tags=["dev-metric"])


@router.post("/metric/run")
def run_metric_dev(req: AgentRequest):
    """
    Metric / evaluator 개발·디버깅 전용
    - LangGraph 전체 파이프라인 재사용
    - issue 개수 + aggregate 판단 확인
    """

    result = run_full_pipeline(
        text=req.text,
        expected=req.expected,
        debug=True,
    )

    def issue_count(res: dict | None) -> int:
        if not res:
            return 0
        return len(res.get("issues", []))

    return {
        "input": req.text,

        # --------------------
        # issue count summary
        # --------------------
        "issue_count": {
            "tone": issue_count(result.get("tone")),
            "logic": issue_count(result.get("logic")),
            "trauma": issue_count(result.get("trauma")),
            "hate_bias": issue_count(result.get("hate_bias")),
            "genre_cliche": issue_count(result.get("genre_cliche")),
            "spelling": issue_count(result.get("spelling")),
        },

        # --------------------
        # aggregate decision
        # --------------------
        "decision": result.get("decision"),
        "aggregated": result.get("aggregated"),

        # --------------------
        # rewrite (if any)
        # --------------------
        "rewrite_guidelines": result.get("rewrite_guidelines"),

        # --------------------
        # persona debug
        # --------------------
        "persona": {
            "reader_persona": result.get("reader_persona"),
            "persona_feedback": result.get("persona_feedback"),
        },
    }
