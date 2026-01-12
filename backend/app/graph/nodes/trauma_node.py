# app/graph/nodes/trauma_node.py
from app.agents import TraumaAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

trauma_agent = TraumaAgent()

@traceable_timed(name="trauma")
def trauma_node(state: AgentState) -> AgentState:
    result = trauma_agent.run(
        split_text=str(state["split_text"])
    )

    return {
        "trauma_result": result
    }
