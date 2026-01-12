# app/services/pipeline_runner.py
import time

from app.graph.graph import agent_app
from app.graph.state import AgentState
from app.observability.langsmith import traceable, create_feedback


@traceable(name="run_full_pipeline")
def run_full_pipeline(
    text: str,
    context: str | None = None,
    expected: dict | None = None,
    debug: bool = False,
) -> dict:
    """
    LangGraph 기반 전체 파이프라인 실행기
    - prod / dev / debug 공용
    """

    # --------------------------------------------------
    # Initial state (entry contract만 만족시키면 충분)
    # --------------------------------------------------
    started_at = time.perf_counter()
    initial_state: AgentState = {
        "original_text": text,
        "context": context,
    }

    # --------------------------------------------------
    # Run graph
    # --------------------------------------------------
    final_state: AgentState = agent_app.invoke(initial_state)
    duration_ms = int((time.perf_counter() - started_at) * 1000)

    # --------------------------------------------------
    # Production output
    # --------------------------------------------------
    decision = (final_state.get("aggregated_result") or {}).get("decision")
    def _issue_count(key: str) -> int:
        data = final_state.get(key) or {}
        return len(data.get("issues", [])) if isinstance(data, dict) else 0

    logic_count = _issue_count("logic_result")
    if logic_count == 0 and "causality_result" in final_state:
        logic_count = _issue_count("causality_result")

    issue_counts = {
        "tone": _issue_count("tone_result"),
        "logic": logic_count,
        "trauma": _issue_count("trauma_result"),
        "hate_bias": _issue_count("hate_bias_result"),
        "genre_cliche": _issue_count("genre_cliche_result"),
        "spelling": _issue_count("spelling_result"),
    }
    has_issues = any(v > 0 for v in issue_counts.values())
    report = final_state.get("final_report") or {}
    report_markdown = report.get("full_report_markdown") if isinstance(report, dict) else None
    report_length = len(report_markdown) if isinstance(report_markdown, str) else 0

    create_feedback([
        {"key": "decision", "value": decision},
        {"key": "issue_counts", "value": issue_counts},
        {"key": "has_issues", "score": 1.0 if has_issues else 0.0, "value": has_issues},
        {"key": "report_length", "value": report_length},
    ])
    _record_eval_feedback(
        expected=expected,
        decision=decision,
        issue_counts=issue_counts,
    )

    if not debug:
        return {
            "final_report": final_state.get("final_report"),
            "decision": decision,
        }

    # --------------------------------------------------
    # Debug / Dev output
    # --------------------------------------------------
    return {
        # core results
        "final_report": final_state.get("final_report"),
        "decision": decision,

        # evaluators
        "tone": final_state.get("tone_result"),
        "logic": final_state.get("logic_result"),
        "trauma": final_state.get("trauma_result"),
        "hate_bias": final_state.get("hate_bias_result"),
        "genre_cliche": final_state.get("genre_cliche_result"),
        "spelling": final_state.get("spelling_result"),

        # persona
        "reader_persona": final_state.get("reader_persona"),
        "persona_feedback": final_state.get("persona_feedback"),

        # aggregate
        "aggregated": final_state.get("aggregated_result"),

        # rewrite
        "rewrite_guidelines": final_state.get("rewrite_guidelines"),
    }


def _record_eval_feedback(
    expected: dict | None,
    decision: str | None,
    issue_counts: dict,
) -> None:
    if not expected:
        return
    entries = []
    expected_decision = expected.get("decision")
    if expected_decision:
        decision_match = expected_decision == decision
        entries.append({
            "key": "eval.decision_match",
            "score": 1.0 if decision_match else 0.0,
            "value": {
                "expected": expected_decision,
                "actual": decision,
            },
        })

    expected_issues = expected.get("issues") or {}
    if expected_issues:
        matches = 0
        total = 0
        for key, expected_present in expected_issues.items():
            if expected_present is None:
                continue
            actual_present = issue_counts.get(key, 0) > 0
            match = bool(expected_present) == actual_present
            total += 1
            matches += 1 if match else 0
            entries.append({
                "key": f"eval.issue_match.{key}",
                "score": 1.0 if match else 0.0,
                "value": {
                    "expected": bool(expected_present),
                    "actual": actual_present,
                },
            })
        if total:
            entries.append({
                "key": "eval.issue_match_rate",
                "score": matches / total,
                "value": {
                    "matches": matches,
                    "total": total,
                },
            })

    if entries:
        create_feedback(entries)

