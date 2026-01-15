# app/graph/nodes/trauma_node.py
from app.agents import TraumaAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

trauma_agent = TraumaAgent()

@traceable_timed(name="trauma")
def trauma_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 3/6 - [Trauma] 트라우마 요소 분석 시작...")
    result = trauma_agent.run(
        state.get("split_text")
    )

    return {
        "trauma_result": result
    }
