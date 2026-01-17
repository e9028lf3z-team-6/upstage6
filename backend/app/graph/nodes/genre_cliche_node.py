# app/graph/nodes/genre_cliche_node.py
from app.agents import GenreClicheAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

genre_cliche_agent = GenreClicheAgent()

@traceable_timed(name="genre_cliche")
def genre_cliche_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 3/6 - [GenreCliche] 장르 클리셰 분석 시작...")
    
    split_text = state.get("split_text")
    if not split_text or (isinstance(split_text, dict) and not split_text.get("split_sentences")):
        logger.warning("genre_cliche_node: No text to analyze.")
        return {"genre_cliche_result": {"issues": [], "score": 10, "note": "분석할 텍스트가 없습니다."}}

    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    try:
        result = genre_cliche_agent.run(
            split_text,
            reader_context=reader_context,
            global_summary=state.get("global_summary")
        )
    except Exception as e:
        logger.error(f"Error in genre_cliche_node: {e}")
        result = {"issues": [], "score": 0, "error": str(e)}

    return {
        "genre_cliche_result": result
    }
