# app/graph/nodes/genre_cliche_node.py
from app.agents import GenreClicheAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

genre_cliche_agent = GenreClicheAgent()

@traceable_timed(name="genre_cliche")
def genre_cliche_node(state: AgentState) -> AgentState:
    result = genre_cliche_agent.run(
        state.get("split_text")
    )

    return {
        "genre_cliche_result": result
    }
