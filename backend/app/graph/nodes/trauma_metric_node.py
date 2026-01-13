# app/graph/nodes/trauma_metric_node.py
from app.graph.state import AgentState
from app.agents.metrics.Trauma_metric import TraumaMetric

trauma_metric = TraumaMetric()

def trauma_metric_node(state: AgentState) -> AgentState:
    trauma_result = state.get("trauma_result") or {}

    metrics = trauma_metric.run(trauma_result)

    return {
        **state,
        "trauma_metrics": metrics
    }
