# app/graph/nodes/spelling_node.py
from app.agents import SpellingAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

spelling_agent = SpellingAgent()

@traceable_timed(name="spelling")
def spelling_node(state: AgentState) -> AgentState:
    result = spelling_agent.run(state.get("split_text"))

    return {
        "spelling_result": result
    }
