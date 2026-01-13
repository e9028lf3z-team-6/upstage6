# app/graph/nodes/tone_validator_node.py
from app.graph.state import AgentState
from app.agents.metrics.tone_Metric import ToneOutputValidator

tone_validator = ToneOutputValidator()

def tone_validator_node(state: AgentState) -> AgentState:
    result = state.get("tone_result") or {}

    validation = tone_validator.validate(result)

    return {
        **state,
        "tone_validation": validation
    }
