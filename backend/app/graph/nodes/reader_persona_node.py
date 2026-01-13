# app/graph/nodes/reader_persona_node.py
from app.agents import ReaderPersonaAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

reader_persona_agent = ReaderPersonaAgent()

@traceable_timed(name="reader_persona")
def reader_persona_node(state: AgentState) -> AgentState:
    result = reader_persona_agent.run(state["context"])
    return {
        "reader_persona": result
    }
