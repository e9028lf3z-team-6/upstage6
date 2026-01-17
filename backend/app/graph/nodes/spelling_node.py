# app/graph/nodes/spelling_node.py
from app.agents import SpellingAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

spelling_agent = SpellingAgent()

@traceable_timed(name="spelling")
def spelling_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 3/6 - [Spelling] 맞춤법 검사 시작...")
    
    split_text = state.get("split_text")
    if not split_text or (isinstance(split_text, dict) and not split_text.get("split_sentences")):
        logger.warning("spelling_node: No text to analyze.")
        return {"spelling_result": {"issues": [], "score": 10, "note": "분석할 텍스트가 없습니다."}}

    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    try:
        result = spelling_agent.run(
            split_text,
            reader_context=reader_context
        )
    except Exception as e:
        logger.error(f"Error in spelling_node: {e}")
        result = {"issues": [], "score": 0, "error": str(e)}

    return {
        "spelling_result": result
    }
