# app/graph/nodes/tone_node.py
from app.agents import ToneEvaluatorAgent
from app.graph.state import AgentState

tone_agent = ToneEvaluatorAgent()

def tone_node(state: AgentState) -> AgentState:
    result = tone_agent.run(
        split_text=str(state["split_text"])
    )

    return {
        **state,
        "tone_result": result
    }
