# app/graph/nodes/final_metric_node.py
from app.agents.metrics.final_metric_agent import FinalMetricAgent
from app.graph.state import AgentState

final_metric_agent = FinalMetricAgent()

def extract_issues(result: dict | None):
    if not result:
        return []
    return result.get("issues", [])

def final_metric_node(state: AgentState) -> AgentState:
    metrics = final_metric_agent.run(
        aggregate=state["aggregated_result"],
        tone_issues=extract_issues(state.get("tone_result")),
        logic_issues=extract_issues(state.get("logic_result")),
        trauma_issues=extract_issues(state.get("trauma_result")),
        hate_issues=extract_issues(state.get("hate_bias_result")),
        cliche_issues=extract_issues(state.get("genre_cliche_result")),
        persona_feedback=state.get("persona_feedback"),
    )

    return {
        **state,
        "final_metrics": metrics
    }
