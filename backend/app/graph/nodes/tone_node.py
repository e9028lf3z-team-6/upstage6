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
    
    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    result = tone_agent.run(
        state.get("split_text"),
        reader_context=reader_context,
        global_summary=state.get("global_summary")
    )

    return {
        "tone_result": result
    }
