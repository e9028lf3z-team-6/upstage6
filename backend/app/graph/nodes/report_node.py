# app/graph/nodes/report_node.py
from app.agents import ComprehensiveReportAgent
from app.graph.state import AgentState

report_agent = ComprehensiveReportAgent()

def extract_issues(result: dict | None):
    if not result:
        return []
    return result.get("issues", [])

def report_node(state: AgentState) -> AgentState:
    report = report_agent.run(
        split_text=state["split_text"],
        tone_issues=extract_issues(state.get("tone_result")),
        logic_issues=extract_issues(state.get("logic_result")),
        trauma_issues=extract_issues(state.get("trauma_result")),
        hate_issues=extract_issues(state.get("hate_bias_result")),
        cliche_issues=extract_issues(state.get("genre_cliche_result")),
        persona_feedback=state.get("persona_feedback"),
    )

    return {
        **state,
        "final_report": report
    }
