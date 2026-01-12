from typing import Any, Dict, Optional

from app.core.settings import get_settings
from app.services.pipeline_runner import run_full_pipeline


async def run_analysis_for_text(
    text: str,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    전체 분석 파이프라인 실행
    - UPSTAGE_API_KEY 있으면 LangGraph + LLM
    - 없으면 로컬 휴리스틱 fallback
    - 항상 동일한 출력 스키마 반환
    """

    settings = get_settings()

    # --------------------------------------------------
    # Full LangGraph pipeline (preferred)
    # --------------------------------------------------
    if settings.upstage_api_key:
        return run_full_pipeline(
            text=text,
            context=context,
            debug=True,
        )

    # --------------------------------------------------
    # Local fallback (LLM 없음, 스키마만 동일)
    # --------------------------------------------------
    tone = _heuristic_tone(text)
    logic = _heuristic_causality(text)
    trauma = _heuristic_trauma(text)
    hate_bias = _heuristic_hate_bias(text)
    genre_cliche = _heuristic_genre_cliche(text)
    spelling = {"issues": []}

    aggregated = {
        "decision": "report",
        "has_issues": any([
            tone["issues"],
            logic["issues"],
            trauma["issues"],
            hate_bias["issues"],
            genre_cliche["issues"],
        ]),
        "summary": "(Mock) UPSTAGE_API_KEY가 없어 로컬 휴리스틱으로 분석했습니다.",
    }

    return {
        # --------------------
        # production-level keys
        # --------------------
        "final_report": {
            "summary": aggregated["summary"],
            "note": "LLM 미사용: 결과는 데모용 휴리스틱입니다.",
        },
        "decision": aggregated["decision"],

        # --------------------
        # evaluators (debug=True 기준)
        # --------------------
        "tone": tone,
        "logic": logic,
        "trauma": trauma,
        "hate_bias": hate_bias,
        "genre_cliche": genre_cliche,
        "spelling": spelling,

        # --------------------
        # persona (fallback은 없음)
        # --------------------
        "reader_persona": None,
        "persona_feedback": None,

        # --------------------
        # aggregate / rewrite
        # --------------------
        "aggregated": aggregated,
        "rewrite_guidelines": None,
    }
