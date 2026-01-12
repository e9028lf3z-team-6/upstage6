# app/graph/nodes/persona_feedback_node.py
from app.agents import PersonaFeedbackAgent
from app.graph.state import AgentState

persona_feedback_agent = PersonaFeedbackAgent()

def persona_feedback_node(state: AgentState) -> AgentState:
    persona = None
    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona")

    result = persona_feedback_agent.run(
        persona=persona,
        split_text=state["split_text"]
    )

    return {
        **state,
        "persona_feedback": result.get("persona_feedback")
    }
