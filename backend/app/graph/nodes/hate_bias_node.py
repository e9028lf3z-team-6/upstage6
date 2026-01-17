# app/graph/nodes/hate_bias_node.py
from app.agents import HateBiasAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

hate_bias_agent = HateBiasAgent()

@traceable_timed(name="hate_bias")
def hate_bias_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 3/6 - [HateBias] 혐오/편향성 분석 시작...")
    
    split_text = state.get("split_text")
    if not split_text or (isinstance(split_text, dict) and not split_text.get("split_sentences")):
        logger.warning("hate_bias_node: No text to analyze.")
        return {"hate_bias_result": {"issues": [], "score": 10, "note": "분석할 텍스트가 없습니다."}}

    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    try:
        result = hate_bias_agent.run(
            split_text,
            reader_context=reader_context
        )
    except Exception as e:
        logger.error(f"Error in hate_bias_node: {e}")
        result = {"issues": [], "score": 0, "error": str(e)}

    return {
        "hate_bias_result": result
    }
