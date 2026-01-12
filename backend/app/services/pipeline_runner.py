# app/services/pipeline_runner.py

from app.agents.tools.split_agent import SplitAgent
from app.agents.tools.tone_agent import ToneEvaluatorAgent
from app.agents.tools.causality_agent import CausalityEvaluatorAgent
from app.agents.tools.TensionCurve_agent import TensionCurveAgent

from app.agents.tools.Trauma_agent import TraumaAgent
from app.agents.tools.HateBias_agent import HateBiasAgent
from app.agents.tools.GenerCliche_agent import GenreClicheAgent

from app.agents.tools.render_persona import ReaderPersonaAgent
from app.agents.tools.persona_feedback import PersonaFeedbackAgent

from app.agents.tools.llm_aggregator import IssueBasedAggregatorAgent
from app.agents.tools.rewrrite_assist import RewriteAssistAgent

from app.agents.metrics.final_metric import FinalMetricAgent
from app.agents.tools.report_agent import ComprehensiveReportAgent


# ---- singleton instances (서비스와 동일)
split_agent = SplitAgent()
tone_agent = ToneEvaluatorAgent()
causality_agent = CausalityEvaluatorAgent()
tension_agent = TensionCurveAgent()

trauma_agent = TraumaAgent()
hate_bias_agent = HateBiasAgent()
genre_cliche_agent = GenreClicheAgent()

persona_agent = ReaderPersonaAgent()
persona_feedback_agent = PersonaFeedbackAgent()

aggregator = IssueBasedAggregatorAgent()
rewrite_agent = RewriteAssistAgent()
final_metric_agent = FinalMetricAgent()
report_agent = ComprehensiveReportAgent()


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
    }

    if debug:
        result["debug"] = {
            "persona": persona,
            "persona_feedback": persona_feedback,
            "reader_context": reader_context,
        }

    return result
