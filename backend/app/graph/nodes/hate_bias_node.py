# app/graph/nodes/hate_bias_node.py
from app.agents import HateBiasAgent
from app.graph.state import AgentState

hate_bias_agent = HateBiasAgent()

def hate_bias_node(state: AgentState) -> AgentState:
    result = hate_bias_agent.run(
        split_text=state["split_text"]
    )

    return {
        **state,
        "hate_bias_result": result
    }
