# app/graph/nodes/rewrite_node.py
from app.agents import RewriteAssistAgent
from app.graph.state import AgentState

rewrite_agent = RewriteAssistAgent()

def extract_issues(result: dict | None):
    if not result:
        return []
    return result.get("issues", [])

def rewrite_node(state: AgentState) -> AgentState:
    result = rewrite_agent.run(
        original_text=state["original_text"],
        split_text=str(state["split_text"]),
        decision_context=state["aggregated_result"],
        tone_issues=extract_issues(state.get("tone_result")),
        logic_issues=extract_issues(state.get("logic_result")),
        trauma_issues=extract_issues(state.get("trauma_result")),
        hate_issues=extract_issues(state.get("hate_bias_result")),
        cliche_issues=extract_issues(state.get("genre_cliche_result")),
        spelling_issues=extract_issues(state.get("spelling_result")),
    )

    return {
        **state,
        "rewrite_guidelines": result
    }
