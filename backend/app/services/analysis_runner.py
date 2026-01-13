from typing import Any, Dict, Optional

from app.core.settings import get_settings
from app.services.pipeline_runner import run_full_pipeline

async def run_analysis_for_text(text: str, mode: str = "full") -> Dict[str, Any]:
    """Run the full multi-agent pipeline.

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
        return run_full_pipeline(text, debug=True, mode=mode)

    # Local fallback: run only split + lightweight heuristics (no LLM).
    # This keeps the pipeline shape similar to the full output.
    split = _split_text(text)

    # Initialize empty
    tone = {}
    causality = {}
    tension = {}
    trauma = {}
    hate = {}
    cliche = {}

    # Run Causality (Always in fallback)
    causality = _heuristic_causality(text)

    if mode == "full":
        tone = _heuristic_tone(text)
        tension = _heuristic_tension(text)
        trauma = _heuristic_trauma(text)
        hate = _heuristic_hate_bias(text)
        cliche = _heuristic_genre_cliche(text)

    aggregate = {
        "summary": "(Mock) UPSTAGE_API_KEY가 없어 로컬 휴리스틱으로 분석했습니다." + (" (로그인 필요)" if mode != "full" else ""),
        "tone_issues": tone.get("issues", []),
        "logic_issues": causality.get("issues", []),
        "tension": tension,
        "trauma_issues": trauma.get("issues", []),
        "hate_issues": hate.get("issues", []),
        "cliche_issues": cliche.get("issues", []),
    }

    final_metric = {
        "reader_level": _guess_reader_level(text) if mode == "full" else "N/A",
        "notes": "LLM 미사용: 결과는 데모용 휴리스틱입니다.",
        "scores": {
            "tone": tone.get("score", 0),
            "causality": causality.get("score", 0),
            "safety": max(trauma.get("score", 0), hate.get("score", 0)),
        }
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
        "hate_bias": hate,
        "genre_cliche": cliche,
        "aggregate": aggregate,
        "final_metric": final_metric,
        "debug": {"mode": f"local_fallback_{mode}"},
    }


def _heuristic_tone(_text: str) -> Dict[str, Any]:
    return {"issues": [], "note": "heuristic_tone_stub"}


def _heuristic_causality(_text: str) -> Dict[str, Any]:
    return {"issues": [], "note": "heuristic_causality_stub"}


def _heuristic_trauma(_text: str) -> Dict[str, Any]:
    return {"issues": [], "note": "heuristic_trauma_stub"}


def _heuristic_hate_bias(_text: str) -> Dict[str, Any]:
    return {"issues": [], "note": "heuristic_hate_bias_stub"}


def _heuristic_genre_cliche(_text: str) -> Dict[str, Any]:
    return {"issues": [], "note": "heuristic_genre_cliche_stub"}
