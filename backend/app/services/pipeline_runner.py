# app/services/pipeline_runner.py

from app.agents.tools.split_agent import SplitAgent
from app.agents.tools.tone_agent import ToneEvaluatorAgent
from app.agents.tools.causality_agent import CausalityEvaluatorAgent
from app.agents.tools.TensionCurve_agent import TensionCurveAgent

from app.agents.tools.Trauma_agent import TraumaAgent
from app.agents.tools.HateBias_agent import HateBiasAgent
from app.agents.tools.GenerCliche_agent import GenreClicheAgent
from app.agents.tools.Spelling_Agent import SpellingAgent

from app.agents.tools.render_persona import ReaderPersonaAgent
from app.agents.tools.persona_feedback import PersonaFeedbackAgent

from app.agents.tools.llm_aggregator import IssueBasedAggregatorAgent
from app.agents.tools.rewrrite_assist import RewriteAssistAgent

from app.agents.metrics.final_metric import FinalMetricAgent


# ---- singleton instances
split_agent = SplitAgent()
tone_agent = ToneEvaluatorAgent()
causality_agent = CausalityEvaluatorAgent()
tension_agent = TensionCurveAgent()

trauma_agent = TraumaAgent()
hate_bias_agent = HateBiasAgent()
genre_cliche_agent = GenreClicheAgent()
spelling_agent = SpellingAgent()

persona_agent = ReaderPersonaAgent()
persona_feedback_agent = PersonaFeedbackAgent()

aggregator = IssueBasedAggregatorAgent()
rewrite_agent = RewriteAssistAgent()
final_metric_agent = FinalMetricAgent()


def run_full_pipeline(text: str, *, debug: bool = False):
    # 1. split
    split_result = split_agent.run(text)

    # 2. persona
    persona = None
    reader_context = None
    try:
        persona = persona_agent.run({
            "text": text,
            "split_text": split_result["split_text"],
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
                split_text=split_result["split_text"],
            )
        except Exception:
            pass

    # 4. agents (evaluation)
    tone = tone_agent.run(split_result["split_text"])
    causality = causality_agent.run(
        split_text=split_result["split_text"],
        reader_context=reader_context,
    )
    tension = tension_agent.run(split_result["split_text"])
    trauma = trauma_agent.run(split_result["split_text"])
    hate = hate_bias_agent.run(split_result["split_text"])
    cliche = genre_cliche_agent.run(split_result["split_text"])

    # 4-1. spelling (surface-level)
    spelling = spelling_agent.run(split_result["split_text"])

    # 5. aggregate
    aggregate = aggregator.run(
        tone_issues=tone.get("issues", []),
        logic_issues=causality.get("issues", []),
        trauma_issues=trauma.get("issues", []),
        hate_issues=hate.get("issues", []),
        cliche_issues=cliche.get("issues", []),
        spelling_issues=spelling.get("issues", []),
        persona_feedback=(
            persona_feedback.get("persona_feedback")
            if persona_feedback else None
        ),
        reader_context=reader_context,
    )

    # 6. rewrite assist (가이드 생성)
    rewrite_assist = rewrite_agent.run(
        original_text=text,
        split_text=split_result["split_text"],
        decision_context=aggregate.dict(),
        tone_issues=tone.get("issues", []),
        logic_issues=causality.get("issues", []),
        trauma_issues=trauma.get("issues", []),
        hate_issues=hate.get("issues", []),
        cliche_issues=cliche.get("issues", []),
        spelling_issues=spelling.get("issues", []),
    )

    # 7. final metric
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

    result = {
        "split": split_result,
        "tone": tone,
        "causality": causality,
        "tension_curve": tension,
        "trauma": trauma,
        "hate_bias": hate,
        "genre_cliche": cliche,
        "spelling": spelling,
        "aggregate": aggregate.dict(),
        "rewrite_assist": rewrite_assist,
        "final_metric": final_metric,
    }

    if debug:
        result["debug"] = {
            "persona": persona,
            "persona_feedback": persona_feedback,
            "reader_context": reader_context,
        }

    return result
