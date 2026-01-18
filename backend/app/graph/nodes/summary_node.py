from app.agents.tools.summary_agent import SummaryAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)
summary_agent = SummaryAgent()

@traceable_timed(name="summarize")
def summary_node(state: AgentState) -> AgentState:
    logger.info("요약 생성: [START]")
    
    logs = add_log("수석 편집자", "반가워요, 작가님! 오늘 가져오신 원고는 어떤 이야기일지 정말 궁금하네요. 저희가 꼼꼼히 읽어보고 좋은 피드백 드릴게요!")
    logs += add_log("수석 편집자", "우선 분석을 시작하기 전에, 제가 글의 전체적인 맥락을 먼저 파악해 보겠습니다.")
    
    # original_text 또는 split_text를 기반으로 요약
    text = state.get("original_text") or ""
    summary = summary_agent.run(text)
    
    logs += add_log("수석 편집자", "글의 핵심 내용을 모두 파악했어요! 이제 각 분야의 전문가 친구들이 세부적으로 살펴볼 차례입니다.")
    
    logger.info("요약 생성: [END]")
    return {
        "global_summary": summary,
        "logs": logs
    }
