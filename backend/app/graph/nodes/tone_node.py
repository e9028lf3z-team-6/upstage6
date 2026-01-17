# app/graph/nodes/tone_node.py
from app.agents import ToneEvaluatorAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

tone_agent = ToneEvaluatorAgent()

@traceable_timed(name="tone")
def tone_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 3/6 - [Tone] 톤앤매너 분석 시작...")
    
    split_text = state.get("split_text")
    if not split_text or (isinstance(split_text, dict) and not split_text.get("split_sentences")):
        logger.warning("tone_node: No text to analyze.")
        return {"tone_result": {"issues": [], "score": 10, "note": "분석할 텍스트가 없습니다."}}

    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    try:
        result = tone_agent.run(
            split_text,
            reader_context=reader_context,
            global_summary=state.get("global_summary")
        )
    except Exception as e:
        logger.error(f"Error in tone_node: {e}")
        result = {"issues": [], "score": 0, "error": str(e)}

    return {
        "tone_result": result
    }
