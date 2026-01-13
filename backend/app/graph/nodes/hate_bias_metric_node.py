# app/graph/nodes/hate_bias_metric_node.py
from app.agents.metrics.HateBias_metric import HateBiasMetricAgent
from app.graph.state import AgentState

hate_bias_metric_agent = HateBiasMetricAgent()

def hate_bias_metric_node(state: AgentState) -> AgentState:
    issues = []
    if state.get("hate_bias_result"):
        issues = state["hate_bias_result"].get("issues", [])

    metrics = hate_bias_metric_agent.run(issues)

    return {
        **state,
        "hate_bias_metrics": metrics
    }
