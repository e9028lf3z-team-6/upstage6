# app/graph/nodes/genre_cliche_node.py
from app.agents import GenreClicheAgent
from app.graph.state import AgentState

genre_cliche_agent = GenreClicheAgent()

def genre_cliche_node(state: AgentState) -> AgentState:
    result = genre_cliche_agent.run(
        split_text=state["split_text"]
    )

    return {
        **state,
        "genre_cliche_result": result
    }
