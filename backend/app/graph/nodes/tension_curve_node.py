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
    result = tension_curve_agent.run(
        state.get("split_text")
    )

    return {
        "tension_curve_result": result
    }
