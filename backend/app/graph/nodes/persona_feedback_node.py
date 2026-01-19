# app/graph/nodes/persona_feedback_node.py
from app.agents import PersonaFeedbackAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

persona_feedback_agent = PersonaFeedbackAgent()

@traceable_timed(name="persona_feedback")
def persona_feedback_node(state: AgentState) -> AgentState:
    logger.info("독자 피드백: [START]")
    persona = None
    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona")

    result = persona_feedback_agent.run(
        persona=persona,
        split_payload=state.get("split_text")
    )
    logger.info("독자 피드백: [END]")

    return {
        "persona_feedback": result.get("persona_feedback")
    }