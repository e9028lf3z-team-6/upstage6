# app/graph/nodes/tension_curve_node.py
from app.agents import TensionCurveAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

tension_curve_agent = TensionCurveAgent()

@traceable_timed(name="tension_curve")
def tension_curve_node(state: AgentState) -> AgentState:
    split_text = state.get("split_text")
    sentences = []
    if isinstance(split_text, dict):
        sentences = split_text.get("split_text", [])
    elif isinstance(split_text, list):
        sentences = split_text

    result = tension_curve_agent.run(
        split_text=sentences
    )

    return {
        "tension_curve_result": result
    }
