# app/graph/nodes/tone_node.py
from app.agents import ToneEvaluatorAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

tone_agent = ToneEvaluatorAgent()

@traceable_timed(name="tone")
def tone_node(state: AgentState) -> AgentState:
    result = tone_agent.run(
        split_text=str(state["split_text"])
    )

    return {
        "tone_result": result
    }
