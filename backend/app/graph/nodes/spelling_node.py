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
    
    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    result = spelling_agent.run(
        state.get("split_text"),
        reader_context=reader_context
    )

    return {
        "spelling_result": result
    }
