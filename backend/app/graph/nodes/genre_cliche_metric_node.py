# app/graph/nodes/genre_cliche_metric_node.py
from app.agents.metrics.genre_cliche_metric import GenreClicheMetricAgent
from app.graph.state import AgentState

genre_cliche_metric_agent = GenreClicheMetricAgent()

def genre_cliche_metric_node(state: AgentState) -> AgentState:
    issues = []
    if state.get("genre_cliche_result"):
        issues = state["genre_cliche_result"].get("issues", [])

    metrics = genre_cliche_metric_agent.run(issues)

    return {
        **state,
        "genre_cliche_metrics": metrics
    }
