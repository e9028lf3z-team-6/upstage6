import os
from typing import Any, Dict

from app.core.settings import get_settings

# Reuse the existing pipeline from the provided agent implementation
from app.services.pipeline_runner import run_full_pipeline

async def run_analysis_for_text(text: str, mode: str = "full") -> Dict[str, Any]:
    """Run the full multi-agent pipeline.

    If UPSTAGE_API_KEY is missing, we still return a deterministic, local-only result
    so the app can be demoed without external calls.
    """
    settings = get_settings()
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
        "split": split,
        "tone": tone,
        "causality": causality,
        "tension_curve": tension,
        "trauma": trauma,
        "hate_bias": hate,
        "genre_cliche": cliche,
        "aggregate": aggregate,
        "final_metric": final_metric,
        "debug": {"mode": f"local_fallback_{mode}"},
    }

def _split_text(text: str) -> dict:
    # naive split by double newline or sentences
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    if not chunks:
        chunks = [text.strip()]
    return {"split_text": chunks, "num_chunks": len(chunks)}

def _heuristic_tone(text: str) -> dict:
    informal = sum(text.count(w) for w in ["ㅋㅋ", "ㅎㅎ", "ㄹㅇ", "쩔", "대박"])
    formal = sum(text.count(w) for w in ["합니다", "드립니다", "~니다"])
    score = 7 if formal>informal else 4
    issues=[]
    if informal>5 and formal>0:
        issues.append({"location": "(전체)", "issue": "격식체와 구어체가 혼재함", "severity": "medium"})
    return {"score": score, "issues": issues}

def _heuristic_causality(text: str) -> dict:
    # look for abrupt transitions words
    abrupt = sum(text.count(w) for w in ["갑자기", "뜬금", "아무튼", "암튼"])
    score = max(1, 8-abrupt)
    issues=[]
    if abrupt>=2:
        issues.append({"location": "(전체)", "issue": "전개 전환이 급격해 보임(휴리스틱)", "severity": "medium"})
    return {"score": score, "issues": issues}

def _heuristic_tension(text: str) -> dict:
    # return simple curve based on paragraph lengths
    paras=[p for p in text.split("\n\n") if p.strip()]
    curve=[]
    for i,p in enumerate(paras[:20]):
        curve.append({"index": i, "tension": min(10, max(1, len(p)//120))})
    return {"curve": curve, "note": "문단 길이 기반 간이 긴장도"}

def _heuristic_trauma(text: str) -> dict:
    keywords=["자해","성폭력","학대","참사","테러","세월호","9.11"]
    hits=[k for k in keywords if k in text]
    issues=[]
    for k in hits:
        issues.append({"location": k, "issue": f"민감 키워드 포함: {k}", "severity": "high"})
    return {"score": 9 if hits else 1, "issues": issues}

def _heuristic_hate_bias(text: str) -> dict:
    keywords=["전라도","여성치고는","노처녀","장애","게이","이민자"]
    hits=[k for k in keywords if k in text]
    issues=[]
    for k in hits:
        issues.append({"location": k, "issue": f"편견/혐오 가능 표현: {k}", "severity": "high"})
    return {"score": 9 if hits else 1, "issues": issues}

def _heuristic_genre_cliche(text: str) -> dict:
    keywords=["회빙환","계약 연애","먼치킨","시한폭탄","USB"]
    hits=[k for k in keywords if k in text]
    issues=[]
    if hits:
        issues.append({"location": "(전체)", "issue": f"장르 클리셰로 보이는 요소: {', '.join(hits)}", "severity": "low"})
    return {"score": 6 if hits else 3, "issues": issues}

def _guess_reader_level(text: str) -> str:
    # simplistic: based on avg word length and jargon
    jargon = sum(text.count(w) for w in ["아키텍처","파라미터","창발","정량","정성","프로세스","메커니즘"])
    if jargon >= 8:
        return "대학원/연구자"
    if jargon >= 3:
        return "대학(학부)"
    return "초/중등"
