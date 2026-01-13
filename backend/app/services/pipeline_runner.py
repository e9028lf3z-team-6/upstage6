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

from app.agents.evaluators.final_evaluator import FinalEvaluatorAgent
from app.agents.tools.report_agent import ComprehensiveReportAgent

# Evaluators
from app.agents.evaluators.tone_evaluator import ToneQualityAgent
from app.agents.evaluators.causality_evaluator import CausalityQualityAgent
from app.agents.evaluators.tension_evaluator import TensionQualityAgent
from app.agents.evaluators.trauma_evaluator import TraumaQualityAgent
from app.agents.evaluators.hatebias_evaluator import HateBiasQualityAgent
from app.agents.evaluators.cliche_evaluator import GenreClicheQualityAgent


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
final_evaluator_agent = FinalEvaluatorAgent()
report_agent = ComprehensiveReportAgent()

# Evaluator instances
tone_quality_agent = ToneQualityAgent()
causality_quality_agent = CausalityQualityAgent()
tension_quality_agent = TensionQualityAgent()
trauma_quality_agent = TraumaQualityAgent()
hatebias_quality_agent = HateBiasQualityAgent()
cliche_quality_agent = GenreClicheQualityAgent()


def run_full_pipeline(text: str, *, debug: bool = False, mode: str = "full"):
    # 1. split
    try:
        split_result = split_agent.run(text)
    except Exception as e:
        print(f"Split agent failed: {e}")
        # fallback
        split_result = {"split_text": [text]}

    # 2. persona (Needed for causality too)
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
    if mode == "full" and persona:
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

    # Initialize empty results
    tone = {"issues": []}
    causality = {"issues": []}
    tension = {"curve": []}
    trauma = {"issues": []}
    hate = {"issues": []}
    cliche = {"issues": []}

    # Run Causality (Always)
    causality = safe_run(causality_agent, split_text=split_result.get("split_text", []), reader_context=reader_context)

    if mode == "full":
        tone = safe_run(tone_agent, split_result.get("split_text", []))
        tension = safe_run(tension_agent, split_result.get("split_text", []))
        trauma = safe_run(trauma_agent, split_result.get("split_text", []))
        hate = safe_run(hate_bias_agent, split_result.get("split_text", []))
        cliche = safe_run(genre_cliche_agent, split_result.get("split_text", []))

    # 5. aggregate
    aggregate = None
    if mode == "full":
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
    else:
        # Mock aggregate for partial run
        aggregate = {"summary": "로그인 후 전체 분석 결과를 확인할 수 있습니다. (개연성 분석만 수행됨)"}

    # 6. final metric
    final_metric = {}
    if mode == "full":
        try:
            final_metric = final_metric_agent.run(
                aggregate=aggregate.dict() if hasattr(aggregate, 'dict') else aggregate,
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
    report = {}
    if mode == "full":
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
    else:
        report = {"full_report_markdown": "# 개연성 분석 리포트\n\n로그인하지 않은 상태에서는 **개연성(Causality)** 분석 결과만 제공됩니다.\n\n## 분석 결과 요약\n" + str(causality.get("issues", []))}

    # 8. Evaluation Scores (QA)
    qa_scores = {}
    try:
        if mode == "full":
            qa_scores["tone"] = tone_quality_agent.run(text, tone).get("score", 0)
            qa_scores["tension"] = tension_quality_agent.run(text, tension).get("score", 0)
            qa_scores["trauma"] = trauma_quality_agent.run(text, trauma).get("score", 0)
            qa_scores["hate_bias"] = hatebias_quality_agent.run(text, hate).get("score", 0)
            qa_scores["cliche"] = cliche_quality_agent.run(text, cliche).get("score", 0)
        
        # Causality is always run
        qa_scores["causality"] = causality_quality_agent.run(text, causality).get("score", 0)

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
        "aggregate": aggregate.dict() if hasattr(aggregate, 'dict') else aggregate,
        "final_metric": final_metric,
        "report": report,
        "qa_scores": qa_scores,
    }

    if debug:
        result["debug"] = {
            "persona": persona,
            "persona_feedback": persona_feedback,
            "reader_context": reader_context,
            "mode": mode
        }

    return result
