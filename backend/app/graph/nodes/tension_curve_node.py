# app/graph/nodes/tension_curve_node.py
from app.agents import TensionCurveAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

tension_curve_agent = TensionCurveAgent()

@traceable_timed(name="tension_curve")
def tension_curve_node(state: AgentState) -> AgentState:
    result = tension_curve_agent.run(
        split_text=state["original_text"]
    )

    return {
        "tension_curve_result": result
    }
