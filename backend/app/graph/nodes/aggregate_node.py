# app/graph/nodes/aggregate_node.py
from app.agents import IssueBasedAggregatorAgent
from app.graph.state import AgentState

aggregator_agent = IssueBasedAggregatorAgent()

def aggregate_node(state: AgentState) -> AgentState:
    def extract_issues(result: dict | None):
        if not result:
            return []
        return result.get("issues", [])

    persona_feedback = None
    reader_context = None

    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona", {})
        reader_context = {
            "knowledge_level": persona.get("knowledge_level")
        }

    aggregate_result = aggregator_agent.run(
        tone_issues=extract_issues(state.get("tone_result")),
        logic_issues=extract_issues(state.get("logic_result")),
        trauma_issues=extract_issues(state.get("trauma_result")),
        hate_issues=extract_issues(state.get("hate_bias_result")),
        cliche_issues=extract_issues(state.get("genre_cliche_result")),
        spelling_issues=extract_issues(state.get("spelling_result")),
        persona_feedback=None,          # 별도 persona evaluator 붙이면 연결
        reader_context=reader_context,
    )

    return {
        **state,
        "aggregated_result": aggregate_result.model_dump(),
    }
