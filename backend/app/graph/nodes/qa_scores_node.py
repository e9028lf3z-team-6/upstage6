# app/graph/nodes/qa_scores_node.py
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

# Note: FinalEvaluatorAgent might still be useful for overall metrics, keeping it optional if needed.
# For now, we focus on aggregating direct scores from analysis agents.

@traceable_timed(name="qa_scores")
def qa_scores_node(state: AgentState) -> AgentState:
    logger.info("점수 집계: [START]")
    
    def get_score(result_key):
        res = state.get(result_key) or {}
        # Return 0 if score is missing or None
        return res.get("score", 0)

    # Aggregate scores directly from analysis results
    qa_scores = {
        "tone": get_score("tone_result"),
        "causality": get_score("logic_result"),  # state key is logic_result or causality_result
        "tension": get_score("tension_curve_result"),
        "trauma": get_score("trauma_result"),
        "hate_bias": get_score("hate_bias_result"),
        "cliche": get_score("genre_cliche_result"),
        "spelling": get_score("spelling_result"),
    }
    
    # Logic result fallback check
    if "causality" not in qa_scores or qa_scores["causality"] == 0:
        if state.get("causality_result"):
             qa_scores["causality"] = state["causality_result"].get("score", 0)

    logger.info(f"점수 집계 완료: {qa_scores}")
    logger.info("점수 집계: [END]")

    return {
        "qa_scores": qa_scores,
        # "final_metric": final_metric, # If needed later
    }