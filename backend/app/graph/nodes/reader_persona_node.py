# app/graph/nodes/reader_persona_node.py
from app.agents import ReaderPersonaAgent
from app.graph.state import AgentState

reader_persona_agent = ReaderPersonaAgent()

def reader_persona_node(state: AgentState) -> AgentState:
    result = reader_persona_agent.run(state["context"])
    return {
        **state,
        "reader_persona": result
    }
