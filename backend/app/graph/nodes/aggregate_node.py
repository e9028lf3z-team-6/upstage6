# app/graph/nodes/aggregate_node.py
from app.agents import IssueBasedAggregatorAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

aggregator_agent = IssueBasedAggregatorAgent()

@traceable_timed(name="aggregate")
def aggregate_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 4/6 - 모든 분석 결과 취합 및 검증 중...")
    def extract_issues(result: dict | None):
        if not result or not isinstance(result, dict):
            return []
        return result.get("issues", [])

    persona_feedback = None
    reader_context = None

    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona", {})
        reader_context = {
            "knowledge_level": persona.get("knowledge_level")
        }

    try:
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
        result_dict = aggregate_result.model_dump()
    except Exception as e:
        logger.error(f"Error in aggregate_node: {e}")
        result_dict = {
            "decision": "report", 
            "summary": f"결과 취합 중 오류가 발생했습니다: {str(e)}",
            "has_issues": False,
            "error": str(e)
        }

    return {
        "aggregated_result": result_dict,
    }
