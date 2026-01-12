# app/graph/nodes/trauma_node.py
from app.agents import TraumaAgent
from app.graph.state import AgentState

trauma_agent = TraumaAgent()

def trauma_node(state: AgentState) -> AgentState:
    result = trauma_agent.run(
        split_text=str(state["split_text"])
    )

    return {
        **state,
        "trauma_result": result
    }
