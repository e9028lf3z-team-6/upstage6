# app/services/pipeline_runner.py
import time

from app.graph.graph import agent_app
from app.graph.state import AgentState
from app.observability.langsmith import traceable, create_feedback

# Evaluators
from app.agents.evaluators.tone_evaluator import ToneQualityAgent
from app.agents.evaluators.causality_evaluator import CausalityQualityAgent
from app.agents.evaluators.tension_evaluator import TensionQualityAgent
from app.agents.evaluators.trauma_evaluator import TraumaQualityAgent
from app.agents.evaluators.hatebias_evaluator import HateBiasQualityAgent
from app.agents.evaluators.cliche_evaluator import GenreClicheQualityAgent


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

trauma_agent = TraumaAgent()
hate_bias_agent = HateBiasAgent()
genre_cliche_agent = GenreClicheAgent()

persona_agent = ReaderPersonaAgent()
persona_feedback_agent = PersonaFeedbackAgent()

aggregator = IssueBasedAggregatorAgent()
rewrite_agent = RewriteAssistAgent()
final_metric_agent = FinalMetricAgent()
report_agent = ComprehensiveReportAgent()

# Evaluator instances
tone_quality_agent = ToneQualityAgent()
causality_quality_agent = CausalityQualityAgent()
tension_quality_agent = TensionQualityAgent()
trauma_quality_agent = TraumaQualityAgent()
hatebias_quality_agent = HateBiasQualityAgent()
cliche_quality_agent = GenreClicheQualityAgent()


def run_full_pipeline(text: str, *, debug: bool = False):
    # 1. split
    try:
        split_result = split_agent.run(text)
    except Exception as e:
        print(f"Split agent failed: {e}")
        # fallback
        split_result = {"split_text": [text]}

    # 2. persona
    persona = None
    reader_context = None
    try:
        persona = persona_agent.run({
            "text": text,
            "split_text": split_result.get("split_text", []),
        })
        reader_context = persona.get("persona")
    except Exception:
        pass

    # 3. persona feedback
    persona_feedback = None
    if persona:
        try:
            persona_feedback = persona_feedback_agent.run(
                persona=persona,
                split_text=split_result.get("split_text", []),
            )
        except Exception:
            pass

    # 4. agents (Robust execution)
    def safe_run(agent, *args, **kwargs):
        try:
            return agent.run(*args, **kwargs)
        except Exception as e:
            print(f"Agent {agent.name} failed: {e}")
            return {"issues": [], "error": str(e)}

    tone = safe_run(tone_agent, split_result.get("split_text", []))
    causality = safe_run(causality_agent, split_text=split_result.get("split_text", []), reader_context=reader_context)
    tension = safe_run(tension_agent, split_result.get("split_text", []))
    trauma = safe_run(trauma_agent, split_result.get("split_text", []))
    hate = safe_run(hate_bias_agent, split_result.get("split_text", []))
    cliche = safe_run(genre_cliche_agent, split_result.get("split_text", []))

    # 5. aggregate
    try:
        aggregate = aggregator.run(
            tone_issues=tone.get("issues", []),
            logic_issues=causality.get("issues", []),
            trauma_issues=trauma.get("issues", []),
            hate_issues=hate.get("issues", []),
            cliche_issues=cliche.get("issues", []),
            persona_feedback=(
                persona_feedback.get("persona_feedback")
                if persona_feedback else None
            ),
            reader_context=reader_context,
        )
    except Exception as e:
        # Fallback aggregate result
        from app.agents.tools.llm_aggregator import AggregateResult
        aggregate = AggregateResult(
            decision="pass", problem_types=[], primary_issue=None, rationale={"error": str(e)}
        )

    # 6. final metric
    try:
        final_metric = final_metric_agent.run(
            aggregate=aggregate.dict(),
            tone_issues=tone.get("issues", []),
            logic_issues=causality.get("issues", []),
            trauma_issues=trauma.get("issues", []),
            hate_issues=hate.get("issues", []),
            cliche_issues=cliche.get("issues", []),
            persona_feedback=(
                persona_feedback.get("persona_feedback")
                if persona_feedback else None
            ),
        )
    except Exception:
        final_metric = {}

    # 7. Comprehensive Report (NEW)
    try:
        report = report_agent.run(
            split_text=split_result,
            tone_issues=tone.get("issues", []),
            logic_issues=causality.get("issues", []),
            trauma_issues=trauma.get("issues", []),
            hate_issues=hate.get("issues", []),
            cliche_issues=cliche.get("issues", []),
            persona_feedback=(
                persona_feedback.get("persona_feedback")
                if persona_feedback else None
            ),
        )
    except Exception as e:
        report = {"error": str(e), "full_report_markdown": "리포트 생성 중 오류가 발생했습니다."}


    # 8. Evaluation Scores (QA)
    qa_scores = {}
    try:
        qa_scores["tone"] = tone_quality_agent.run(text, tone).get("score", 0)
        qa_scores["causality"] = causality_quality_agent.run(text, causality).get("score", 0)
        qa_scores["tension"] = tension_quality_agent.run(text, tension).get("score", 0)
        qa_scores["trauma"] = trauma_quality_agent.run(text, trauma).get("score", 0)
        qa_scores["hate_bias"] = hatebias_quality_agent.run(text, hate).get("score", 0)
        qa_scores["cliche"] = cliche_quality_agent.run(text, cliche).get("score", 0)
    except Exception as e:
        print(f"QA Evaluation failed: {e}")

    result = {
        "split": split_result,
        "tone": tone,
        "causality": causality,
        "tension_curve": tension,
        "trauma": trauma,
        "hate_bias": hate,
        "genre_cliche": cliche,
        "aggregate": aggregate.dict(),
        "final_metric": final_metric,
        "report": report,  # Added report
        "qa_scores": qa_scores, # Added scores
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

