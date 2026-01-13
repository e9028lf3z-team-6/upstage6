# app/graph/nodes/report_node.py
from app.agents import ComprehensiveReportAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

report_agent = ComprehensiveReportAgent()

def extract_issues(result: dict | None):
    if not result:
        return []
    return result.get("issues", [])

@traceable_timed(name="report")
def report_node(state: AgentState) -> AgentState:
    # SplitAgent 제거로 인해 original_text를 split_text 구조로 래핑하여 전달
    original_text = state.get("original_text", "")
    mock_split_text = {"split_text": [original_text]}

    report = report_agent.run(
        split_text=mock_split_text,
        tone_issues=extract_issues(state.get("tone_result")),
        logic_issues=extract_issues(state.get("logic_result")),
        trauma_issues=extract_issues(state.get("trauma_result")),
        hate_issues=extract_issues(state.get("hate_bias_result")),
        cliche_issues=extract_issues(state.get("genre_cliche_result")),
        persona_feedback=state.get("persona_feedback"),
    )

    return {
        "final_report": report
    }
