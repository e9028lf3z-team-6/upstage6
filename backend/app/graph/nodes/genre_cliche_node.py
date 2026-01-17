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
    
    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    result = genre_cliche_agent.run(
        state.get("split_text"),
        reader_context=reader_context,
        global_summary=state.get("global_summary")
    )

    return {
        "genre_cliche_result": result
    }
