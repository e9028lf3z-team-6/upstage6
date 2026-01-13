# app/graph/nodes/qa_scores_node.py
from app.agents.evaluators.tone_evaluator import ToneQualityAgent
from app.agents.evaluators.causality_evaluator import CausalityQualityAgent
from app.agents.evaluators.tension_evaluator import TensionQualityAgent
from app.agents.evaluators.trauma_evaluator import TraumaQualityAgent
from app.agents.evaluators.hatebias_evaluator import HateBiasQualityAgent
from app.agents.evaluators.cliche_evaluator import GenreClicheQualityAgent
from app.agents.evaluators.spelling_evaluator import SpellingQualityAgent
from app.agents.evaluators.final_evaluator import FinalEvaluatorAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

tone_quality_agent = ToneQualityAgent()
causality_quality_agent = CausalityQualityAgent()
tension_quality_agent = TensionQualityAgent()
trauma_quality_agent = TraumaQualityAgent()
hate_bias_quality_agent = HateBiasQualityAgent()
cliche_quality_agent = GenreClicheQualityAgent()
spelling_quality_agent = SpellingQualityAgent()
final_evaluator_agent = FinalEvaluatorAgent()


def _safe_score(agent, name: str, *args) -> dict:
    try:
        result = agent.run(*args)
        if not isinstance(result, dict):
            result = {}
    except Exception as exc:
        result = {"error": str(exc)}
    if "score" not in result:
        result["score"] = 0
    result.setdefault("name", name)
    return result


@traceable_timed(name="qa_scores")
def qa_scores_node(state: AgentState) -> AgentState:
    original_text = state.get("original_text") or ""
    logic_result = state.get("logic_result") or state.get("causality_result") or {}

    tone_eval = _safe_score(tone_quality_agent, "tone", original_text, state.get("tone_result") or {})
    logic_eval = _safe_score(causality_quality_agent, "causality", original_text, logic_result)
    tension_eval = _safe_score(
        tension_quality_agent, "tension", original_text, state.get("tension_curve_result") or {}
    )
    trauma_eval = _safe_score(trauma_quality_agent, "trauma", original_text, state.get("trauma_result") or {})
    hate_eval = _safe_score(hate_bias_quality_agent, "hate_bias", original_text, state.get("hate_bias_result") or {})
    cliche_eval = _safe_score(cliche_quality_agent, "genre_cliche", original_text, state.get("genre_cliche_result") or {})
    spelling_eval = _safe_score(spelling_quality_agent, "spelling", original_text, state.get("spelling_result") or {})

    qa_scores = {
        "tone": tone_eval.get("score", 0),
        "causality": logic_eval.get("score", 0),
        "tension": tension_eval.get("score", 0),
        "trauma": trauma_eval.get("score", 0),
        "hate_bias": hate_eval.get("score", 0),
        "cliche": cliche_eval.get("score", 0),
        "spelling": spelling_eval.get("score", 0),
    }

    aggregate = state.get("aggregated_result") or {}
    final_metric = {}
    try:
        final_metric = final_evaluator_agent.run(
            aggregate=aggregate,
            tone_issues=(state.get("tone_result") or {}).get("issues", []),
            logic_issues=logic_result.get("issues", []),
            trauma_issues=(state.get("trauma_result") or {}).get("issues", []),
            hate_issues=(state.get("hate_bias_result") or {}).get("issues", []),
            cliche_issues=(state.get("genre_cliche_result") or {}).get("issues", []),
            persona_feedback=state.get("persona_feedback"),
        )
    except Exception as exc:
        final_metric = {"error": str(exc)}

    return {
        "qa_scores": qa_scores,
        "final_metric": final_metric,
    }
