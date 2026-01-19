# app/graph/nodes/report_node.py
from app.agents import ComprehensiveReportAgent
from app.agents.utils import extract_split_payload
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
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
    logger.info("리포트 생성: [START]")
    logs = add_log("수석 편집자", "모든 전문가들의 의견이 도착했네요! 제가 작가님께 도움이 될 만한 핵심 내용들만 쏙쏙 뽑아서 리포트로 정리해 드릴게요.")
    
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
    
    logs += add_log("수석 편집자", "드디어 작가님만을 위한 맞춤 리포트가 완성되었습니다! 오른쪽 패널에서 바로 확인해 보실 수 있어요. 작가님의 멋진 집필 활동을 항상 응원합니다! ✨")
    
    logger.info("리포트 생성: [END]")
    return {
        "final_report": report,
        "logs": logs
    }
