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
    
    reader_context = None
    if state.get("reader_persona"):
        reader_context = state["reader_persona"].get("persona", {})

    result = hate_bias_agent.run(
        state.get("split_text"),
        reader_context=reader_context
    )

    return {
        "hate_bias_result": result
    }
