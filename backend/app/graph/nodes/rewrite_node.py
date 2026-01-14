# app/graph/nodes/rewrite_node.py
from app.agents import RewriteAssistAgent
from app.agents.utils import extract_split_payload
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

rewrite_agent = RewriteAssistAgent()

def extract_issues(result: dict | None):
    if not result:
        return []
    return result.get("issues", [])

@traceable_timed(name="rewrite")
def rewrite_node(state: AgentState) -> AgentState:
    split_summary, split_sentences = extract_split_payload(state.get("split_text"))
    if not split_summary and split_sentences:
        split_summary = "\n".join(split_sentences[:5])
    result = rewrite_agent.run(
        original_text=state["original_text"],
        split_text=split_summary,
        decision_context=state["aggregated_result"],
        tone_issues=extract_issues(state.get("tone_result")),
        logic_issues=extract_issues(state.get("logic_result")),
        trauma_issues=extract_issues(state.get("trauma_result")),
        hate_issues=extract_issues(state.get("hate_bias_result")),
        cliche_issues=extract_issues(state.get("genre_cliche_result")),
        spelling_issues=extract_issues(state.get("spelling_result")),
    )

    return {
        "rewrite_guidelines": result
    }
