from app.agents import TraumaAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

trauma_agent = TraumaAgent()

@traceable_timed(name="trauma")
def trauma_node(state: AgentState) -> AgentState:
    logger.info("트라우마 분석: [START]")
    logs = add_log("안전 관리자", "혹시 독자들에게 상처가 될 만한 민감한 묘사가 있는지 조심스럽게 살펴볼게요. 안전이 제일이니까요!")
    
    result = trauma_agent.run(
        state.get("split_text")
    )
    
    issue_count = len(result.get("issues", []))
    if issue_count > 0:
        logs += add_log("안전 관리자", f"작가님, 독자들이 조금 주의 깊게 읽어야 할 표현을 {issue_count}건 정도 발견했어요. 리포트에 조언을 담아두었습니다.")
    else:
        logs += add_log("안전 관리자", "안전 점검 완료! 모든 연령의 독자들이 편안하게 읽을 수 있는 세심한 배려가 느껴지는 글이네요.")
        
    logger.info("트라우마 분석: [END]")
    return {
        "trauma_result": result,
        "logs": logs
    }
