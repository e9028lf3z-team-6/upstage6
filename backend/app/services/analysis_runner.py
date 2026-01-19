import logging
import time
from typing import Any, Dict, Optional

from app.core.settings import get_settings
from app.graph.graph import agent_app
from app.graph.state import AgentState
from app.agents.tools.split import Splitter
from app.agents.tools.causality_agent import CausalityEvaluatorAgent
from app.agents.tools.llm_aggregator import IssueBasedAggregatorAgent
# Evaluators removed
# from app.agents.evaluators.final_evaluator import FinalEvaluatorAgent
# ... imports removed ...

from app.observability.langsmith import traceable
from app.llm.client import has_upstage_api_key
from app.services.split_map import build_split_payload
from app.services.issue_normalizer import normalize_issues

logger = logging.getLogger(__name__)

# ... (omitted) ...

def _run_final_evaluator(outputs: Dict[str, Any]) -> Dict[str, Any]:
    # FinalEvaluatorAgent is removed
    return {} 
    
    # Original Logic (commented out for reference)
    # final_evaluator = FinalEvaluatorAgent()
    # aggregate = outputs.get("aggregate") or outputs.get("aggregated") or {}
    # if hasattr(aggregate, "dict"):
    #     aggregate = aggregate.dict()
    # try:
    #     return final_evaluator.run(
    #         aggregate=aggregate,
    #         tone_issues=(outputs.get("tone") or {}).get("issues", []),
    #         logic_issues=(outputs.get("logic") or {}).get("issues", []),
    #         trauma_issues=(outputs.get("trauma") or {}).get("issues", []),
    #         hate_issues=(outputs.get("hate_bias") or {}).get("issues", []),
    #         cliche_issues=(outputs.get("genre_cliche") or {}).get("issues", []),
    #         persona_feedback=outputs.get("persona_feedback"),
    #     )
    # except Exception as exc:
    #     return {"error": str(exc)}
from app.llm.client import has_upstage_api_key
from app.services.split_map import build_split_payload
from app.services.issue_normalizer import normalize_issues

logger = logging.getLogger(__name__)

@traceable(name="analysis_run", run_type="chain")
async def run_analysis_for_text(
    text: str,
    context: Optional[str] = None,
    mode: str = "full",
) -> Dict[str, Any]:
    # ... (기존 코드 유지)
    if has_upstage_api_key():
        if mode == "full":
            return await _run_langgraph_full(text=text, context=context, mode=mode)
        return _run_causality_only(text=text, mode=mode)
    # ...

async def stream_analysis_for_text(
    text: str,
    context: Optional[str] = None,
    mode: str = "full",
):
    """
    분석 과정을 실시간으로 스트리밍하는 비동기 제너레이터
    """
    logger.info(f"[STREAM] Start streaming. Mode: {mode}, API_KEY: {has_upstage_api_key()}")

    if not has_upstage_api_key() or mode != "full":
        logger.info(f"[STREAM] Entering non-full/fallback mode. Mode: {mode}")
        # 폴백이나 제한 모드일 경우 즉시 결과 반환
        yield {"type": "log", "agent": "코디네이터", "logs": [{"agent": "코디네이터", "message": "작가님, 제가 가벼운 마음으로 먼저 훑어볼게요! 상세 분석은 로그인이 필요하지만, 기본적인 것부터 도와드릴게요.", "timestamp": time.time()}]}
        
        logger.info(f"[STREAM] Running run_analysis_for_text for mode: {mode}")
        res = await run_analysis_for_text(text, context, mode)
        logger.info(f"[STREAM] run_analysis_for_text completed.")
        
        yield {"type": "final_result", "data": res}
        return

    initial_state: AgentState = {
        "original_text": text,
        "context": context,
        "logs": []
    }

    # 누적된 최종 상태를 담을 변수
    accumulated_state = initial_state.copy()

    # 노드 이름 매핑 (가독성용)
    node_labels = {
        "reader_persona": "독자 페르소나 설정",
        "split": "문장 분리 중",
        "summary": "전체 맥락 요약",
        "persona_feedback": "페르소나 맞춤 피드백",
        "tone": "말투/어조 분석",
        "logic": "개연성/논리 분석",
        "trauma": "트라우마 유발 요소 검사",
        "hate_bias": "혐오/편향 표현 검사",
        "genre_cliche": "장르 클리셰 분석",
        "spelling": "맞춤법 검사",
        "tension_curve": "긴장도 곡선 생성",
        "aggregate": "분석 결과 종합",
        "report": "최종 리포트 작성",
        "qa_scores": "품질 점수 산정"
    }

    try:
        async for event in agent_app.astream(initial_state, stream_mode="updates"):
            for node_name, state_update in event.items():
                try:
                    # 상태 누적
                    accumulated_state.update(state_update)
                    
                    label = node_labels.get(node_name, node_name)
                    
                    # 1. 노드에서 발생한 실제 로그 전송
                    if "logs" in state_update and state_update["logs"]:
                        yield {"type": "log", "agent": node_name, "logs": state_update["logs"]}
                    else:
                        # 2. 로그가 없는 노드일 경우 단순 진행 상황 알림
                        yield {"type": "log", "agent": "코디네이터", "logs": [{"agent": "코디네이터", "message": f"'{label}' 단계를 끝냈어요!", "timestamp": time.time()}]}
                    
                    yield {"type": "node_complete", "node": node_name}
                except Exception as node_err:
                    logger.error(f"[STREAM] Node update error ({node_name}): {node_err}")

        # 최종 결과 구성
        res = await _build_final_result(accumulated_state, text, context, mode)
        yield {"type": "final_result", "data": res}
        
    except Exception as e:
        logger.error(f"[STREAM] Critical Error: {e}", exc_info=True)
        yield {"type": "error", "message": str(e)}

async def _build_final_result(final_state: AgentState, text: str, context: Optional[str], mode: str) -> Dict[str, Any]:
    """최종 상태를 분석 결과 딕셔너리로 변환 (ainvoke 없이)"""
    aggregated = final_state.get("aggregated_result") or {}
    decision = aggregated.get("decision")
    final_report = final_state.get("final_report")
    logic = final_state.get("logic_result") or final_state.get("causality_result")
    tension = final_state.get("tension_curve_result")

    split_payload = final_state.get("split_text") or {}
    if isinstance(split_payload, list):
        split_payload = {"split_sentences": [str(item) for item in split_payload], "split_map": []}
    elif isinstance(split_payload, str):
        split_payload = build_split_payload(split_payload)
    elif not isinstance(split_payload, dict):
        split_payload = {}

    result = {
        "split": split_payload,
        "final_report": final_report,
        "report": final_report,
        "decision": decision,
        "tone": final_state.get("tone_result"),
        "logic": logic,
        "trauma": final_state.get("trauma_result"),
        "hate_bias": final_state.get("hate_bias_result"),
        "genre_cliche": final_state.get("genre_cliche_result"),
        "spelling": final_state.get("spelling_result"),
        "tension_curve": tension,
        "causality": logic,
        "aggregate": aggregated,
        "aggregated": aggregated,
        "reader_persona": final_state.get("reader_persona"),
        "persona_feedback": final_state.get("persona_feedback"),
        "rewrite_guidelines": final_state.get("rewrite_guidelines"),
        "logs": final_state.get("logs", []),
        "debug": {"mode": f"langgraph_stream_{mode}"},
    }

    result["final_metric"] = final_state.get("final_metric") or _run_final_evaluator(result)
    result["qa_scores"] = final_state.get("qa_scores") or _run_qa_scores(text, result, mode="full")
    _apply_optional_outputs(result, split_payload)

    return result


def _apply_optional_outputs(result: Dict[str, Any], split_payload: dict | None) -> None:
    settings = get_settings()
    if not isinstance(split_payload, dict):
        split_payload = {}

    if settings.enable_normalized_issues:
        normalized_issues, highlights = normalize_issues(result, split_payload)
        result["normalized_issues"] = normalized_issues
        result["highlights"] = highlights

    if settings.enable_split_map:
        result["split_sentences"] = split_payload.get("split_sentences")
        result["split_map"] = split_payload.get("split_map")


async def _run_langgraph_full(text: str, context: Optional[str], mode: str) -> Dict[str, Any]:
    logger.info("[DEBUG] _run_langgraph_full: Preparing initial state.")
    initial_state: AgentState = {
        "original_text": text,
        "context": context,
    }
    logger.info("[DEBUG] _run_langgraph_full: Invoking agent_app (LangGraph).")
    try:
        final_state: AgentState = await agent_app.ainvoke(initial_state)
        logger.info("[DEBUG] _run_langgraph_full: agent_app returned successfully.")
    except Exception as e:
        logger.error(f"[DEBUG] _run_langgraph_full: agent_app failed with error: {e}")
        raise e

    aggregated = final_state.get("aggregated_result") or {}
    decision = aggregated.get("decision")
    final_report = final_state.get("final_report")
    logic = final_state.get("logic_result") or final_state.get("causality_result")
    tension = final_state.get("tension_curve_result")

    split_payload = final_state.get("split_text") or {}
    if isinstance(split_payload, list):
        split_payload = {
            "split_sentences": [str(item) for item in split_payload],
            "split_map": [],
        }
    elif isinstance(split_payload, str):
        split_payload = build_split_payload(split_payload)
    elif not isinstance(split_payload, dict):
        split_payload = {}

    result = {
        "split": split_payload,
        "final_report": final_report,
        "report": final_report,
        "decision": decision,
        "tone": final_state.get("tone_result"),
        "logic": logic,
        "trauma": final_state.get("trauma_result"),
        "hate_bias": final_state.get("hate_bias_result"),
        "genre_cliche": final_state.get("genre_cliche_result"),
        "spelling": final_state.get("spelling_result"),
        "tension_curve": tension,
        "causality": logic,
        "aggregate": aggregated,
        "aggregated": aggregated,
        "reader_persona": final_state.get("reader_persona"),
        "persona_feedback": final_state.get("persona_feedback"),
        "rewrite_guidelines": final_state.get("rewrite_guidelines"),
        "logs": final_state.get("logs", []),
        "debug": {"mode": f"langgraph_{mode}"},
    }

    result["final_metric"] = final_state.get("final_metric") or _run_final_evaluator(result)
    result["qa_scores"] = final_state.get("qa_scores") or _run_qa_scores(text, result, mode="full")
    _apply_optional_outputs(result, split_payload)

    return result


def _run_causality_only(text: str, mode: str) -> Dict[str, Any]:
    logger.info("[DEBUG] _run_causality_only: Starting.")
    splitter = Splitter()
    causality_agent = CausalityEvaluatorAgent()
    aggregator = IssueBasedAggregatorAgent()

    try:
        logger.info("[DEBUG] _run_causality_only: Running Splitter.")
        split_result = splitter.run(text)
        logger.info("[DEBUG] _run_causality_only: Splitter finished.")
    except Exception as e:
        logger.error(f"[DEBUG] _run_causality_only: Splitter failed: {e}")
        split_result = build_split_payload(text)

    causality = {}
    try:
        logger.info("[DEBUG] _run_causality_only: Running CausalityEvaluatorAgent.")
        causality = causality_agent.run(
            split_result,
            reader_context=None,
        )
        logger.info("[DEBUG] _run_causality_only: CausalityEvaluatorAgent finished.")
    except Exception as e:
        logger.error(f"[DEBUG] _run_causality_only: CausalityEvaluatorAgent failed: {e}")
        causality = {"issues": [], "error": "causality agent failed"}

    aggregate = aggregator.run(
        tone_issues=[],
        logic_issues=causality.get("issues", []),
        trauma_issues=[],
        hate_issues=[],
        cliche_issues=[],
        persona_feedback=None,
        reader_context=None,
    )

    report = {
        "full_report_markdown": (
            "# 개연성 분석 리포트\n\n"
            "로그인하지 않은 상태에서는 **개연성(Causality)** 분석 결과만 제공됩니다.\n\n"
            "## 분석 결과 요약\n"
            + str(causality.get("issues", []))
        )
    }

    result = {
        "split": split_result,
        "final_report": report,
        "report": report,
        "decision": aggregate.decision if hasattr(aggregate, "decision") else None,
        "tone": {"issues": []},
        "logic": causality,
        "causality": causality,
        "trauma": {"issues": []},
        "hate_bias": {"issues": []},
        "genre_cliche": {"issues": []},
        "spelling": {"issues": []},
        "tension_curve": {"curve": []},
        "aggregate": aggregate.dict() if hasattr(aggregate, "dict") else aggregate,
        "aggregated": aggregate.dict() if hasattr(aggregate, "dict") else aggregate,
        "final_metric": {},
        "qa_scores": _run_qa_scores(text, {"causality": causality}, mode="causality_only"),
        "debug": {"mode": f"langgraph_{mode}"},
    }
    _apply_optional_outputs(result, split_result)
    return result


def _run_fallback(text: str, mode: str) -> Dict[str, Any]:
    split = _split_text(text)

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
        "summary": "(Mock) UPSTAGE_API_KEY가 없어 로컬 휴리스틱으로 분석했습니다."
        + (" (로그인 필요)" if mode != "full" else ""),
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
        },
    }

    final_report = {
        "summary": aggregate["summary"],
        "note": "LLM 미사용: 결과는 데모용 휴리스틱입니다.",
    }

    result = {
        "split": split,
        "tone": tone,
        "logic": causality,
        "causality": causality,
        "trauma": trauma,
        "hate_bias": hate,
        "genre_cliche": cliche,
        "spelling": {"issues": []},
        "aggregate": aggregate,
        "final_metric": final_metric,
        "final_report": final_report,
        "report": final_report,
        "decision": None,
        "debug": {"mode": f"local_fallback_{mode}"},
    }
    _apply_optional_outputs(result, split)
    return result


def _run_final_evaluator(outputs: Dict[str, Any]) -> Dict[str, Any]:
    # FinalEvaluatorAgent removed
    return {}


def _run_qa_scores(text: str, outputs: Dict[str, Any], mode: str) -> Dict[str, int]:
    scores: Dict[str, int] = {}
    
    def get_score(key_name):
        obj = outputs.get(key_name) or {}
        return obj.get("score", 0)

    # Causality is always run
    scores["causality"] = get_score("causality") or get_score("logic")

    if mode == "full":
        scores["tone"] = get_score("tone")
        scores["tension"] = get_score("tension_curve")
        scores["trauma"] = get_score("trauma")
        scores["hate_bias"] = get_score("hate_bias")
        scores["cliche"] = get_score("genre_cliche")
        scores["spelling"] = get_score("spelling")
    
    return scores


def _split_text(text: str) -> dict:
    return build_split_payload(text)


def _heuristic_tone(text: str) -> dict:
    informal = sum(text.count(w) for w in ["ㅋㅋ", "ㅎㅎ", "ㄹㅇ", "쩔", "대박"])
    formal = sum(text.count(w) for w in ["합니다", "드립니다", "~니다"])
    score = 7 if formal > informal else 4
    issues = []
    if informal > 5 and formal > 0:
        issues.append({"location": "(전체)", "issue": "격식체와 구어체가 혼재함", "severity": "medium"})
    return {"score": score, "issues": issues}


def _heuristic_causality(text: str) -> dict:
    abrupt = sum(text.count(w) for w in ["갑자기", "뜬금", "아무튼", "암튼"])
    score = max(1, 8 - abrupt)
    issues = []
    if abrupt >= 2:
        issues.append({"location": "(전체)", "issue": "전개 전환이 급격해 보임(휴리스틱)", "severity": "medium"})
    return {"score": score, "issues": issues}


def _heuristic_tension(text: str) -> dict:
    paras = [p for p in text.split("\n\n") if p.strip()]
    curve = []
    for i, p in enumerate(paras[:20]):
        curve.append({"index": i, "tension": min(10, max(1, len(p) // 120))})
    return {"curve": curve, "note": "문단 길이 기반 간이 긴장도"}


def _heuristic_trauma(text: str) -> dict:
    keywords = ["자해", "성폭력", "학대", "참사", "테러", "세월호", "9.11"]
    hits = [k for k in keywords if k in text]
    issues = []
    for k in hits:
        issues.append({"location": k, "issue": f"민감 키워드 포함: {k}", "severity": "high"})
    return {"score": 9 if hits else 1, "issues": issues}


def _heuristic_hate_bias(text: str) -> dict:
    keywords = ["전라도", "여성치고는", "노처녀", "장애", "게이", "이민자"]
    hits = [k for k in keywords if k in text]
    issues = []
    for k in hits:
        issues.append({"location": k, "issue": f"편견/혐오 가능 표현: {k}", "severity": "high"})
    return {"score": 9 if hits else 1, "issues": issues}


def _heuristic_genre_cliche(text: str) -> dict:
    keywords = ["회빙환", "계약 연애", "먼치킨", "시한폭탄", "USB"]
    hits = [k for k in keywords if k in text]
    issues = []
    if hits:
        issues.append({"location": "(전체)", "issue": f"장르 클리셰로 보이는 요소: {', '.join(hits)}", "severity": "low"})
    return {"score": 6 if hits else 3, "issues": issues}


def _guess_reader_level(text: str) -> str:
    jargon = sum(text.count(w) for w in ["아키텍처", "파라미터", "창발", "정량", "정성", "프로세스", "메커니즘"])
    if jargon >= 8:
        return "대학원/연구자"
    if jargon >= 3:
        return "대학(학부)"
    return "초/중등"
