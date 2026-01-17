# app/graph/nodes/tension_curve_node.py
from app.agents import TensionCurveAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

tension_curve_agent = TensionCurveAgent()

@traceable_timed(name="tension_curve")
def tension_curve_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 3/6 - [Tension] 긴장감 곡선 분석 시작...")
    
    split_text = state.get("split_text")
    if not split_text or (isinstance(split_text, dict) and not split_text.get("split_sentences")):
        logger.warning("tension_curve_node: No text to analyze.")
        return {"tension_curve_result": {"curve": [], "note": "분석할 텍스트가 없습니다."}}

    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    try:
        result = tension_curve_agent.run(
            split_text,
            reader_context=reader_context
        )
    except Exception as e:
        logger.error(f"Error in tension_curve_node: {e}")
        result = {"curve": [], "note": f"오류 발생: {str(e)}", "error": str(e)}

    return {
        "tension_curve_result": result
    }
