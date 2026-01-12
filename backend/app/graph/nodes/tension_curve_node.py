# app/graph/nodes/tension_curve_node.py
from app.agents.tension_curve_agent import TensionCurveAgent
from app.graph.state import AgentState

tension_curve_agent = TensionCurveAgent()

def tension_curve_node(state: AgentState) -> AgentState:
    result = tension_curve_agent.run(
        split_text=str(state["split_text"])
    )

    return {
        **state,
        "tension_curve_result": result
    }
