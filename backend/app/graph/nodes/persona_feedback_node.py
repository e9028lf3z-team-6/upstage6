# app/graph/nodes/persona_feedback_node.py
from app.agents import PersonaFeedbackAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

persona_feedback_agent = PersonaFeedbackAgent()

@traceable_timed(name="persona_feedback")
def persona_feedback_node(state: AgentState) -> AgentState:
    persona = None
    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona")

    result = persona_feedback_agent.run(
        persona=persona,
        split_payload=state.get("split_text")
    )

    return {
        "persona_feedback": result.get("persona_feedback")
    }
