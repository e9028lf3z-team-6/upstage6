# app/graph/nodes/hate_bias_node.py
from app.agents import HateBiasAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

hate_bias_agent = HateBiasAgent()

@traceable_timed(name="hate_bias")
def hate_bias_node(state: AgentState) -> AgentState:
    result = hate_bias_agent.run(
        state.get("split_text")
    )

    return {
        "hate_bias_result": result
    }
