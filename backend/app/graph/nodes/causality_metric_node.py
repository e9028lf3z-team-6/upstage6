# app/graph/nodes/causality_metric_node.py
from app.agents.metrics.causality_metric import CausalityMetricAgent
from app.graph.state import AgentState

causality_metric_agent = CausalityMetricAgent()

def causality_metric_node(state: AgentState) -> AgentState:
    issues = []
    if state.get("causality_result"):
        issues = state["causality_result"].get("issues", [])

    reader_context = None
    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona", {})
        reader_context = {
            "knowledge_level": persona.get("knowledge_level")
        }

    metrics = causality_metric_agent.run(
        issues=issues,
        reader_context=reader_context,
    )

    return {
        **state,
        "causality_metrics": metrics
    }
