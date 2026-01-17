# app/graph/nodes/report_node.py
from app.agents import ComprehensiveReportAgent
from app.agents.utils import extract_split_payload
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

report_agent = ComprehensiveReportAgent()

def extract_issues(result: dict | None):
    if not result:
        return []
    return result.get("issues", [])

@traceable_timed(name="report")
def report_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 5/6 - 최종 분석 리포트 생성 중...")
    
    try:
        split_summary, split_sentences = extract_split_payload(state.get("split_text"))
        
        report = report_agent.run(
            split_text={
                "summary": split_summary,
                "sentences": split_sentences,
            },
            tone_issues=extract_issues(state.get("tone_result")),
            logic_issues=extract_issues(state.get("logic_result")),
            trauma_issues=extract_issues(state.get("trauma_result")),
            hate_issues=extract_issues(state.get("hate_bias_result")),
            cliche_issues=extract_issues(state.get("genre_cliche_result")),
            persona_feedback=state.get("persona_feedback"),
        )
    except Exception as e:
        logger.error(f"Error in report_node: {e}")
        report = {
            "full_report_markdown": f"# 분석 리포트 생성 실패\n\n오류가 발생하여 리포트를 생성할 수 없습니다: {str(e)}",
            "error": str(e)
        }

    return {
        "final_report": report
    }
