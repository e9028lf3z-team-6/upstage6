# app/graph/nodes/causality_node.py
from app.agents import CausalityEvaluatorAgent
from app.graph.state import AgentState

causality_agent = CausalityEvaluatorAgent()

def causality_node(state: AgentState) -> AgentState:
    reader_context = None

    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona", {})
        reader_context = {
            "knowledge_level": persona.get("knowledge_level", "중급")
        }

    result = causality_agent.run(
        split_text=state["split_text"],
        reader_context=reader_context
    )

    return {
        **state,
        "causality_result": result
    }
