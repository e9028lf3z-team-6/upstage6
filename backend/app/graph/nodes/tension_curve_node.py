from app.agents import TensionCurveAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

tension_curve_agent = TensionCurveAgent()

@traceable_timed(name="tension_curve")
def tension_curve_node(state: AgentState) -> AgentState:
    logger.info("긴장감 분석: [START]")
    logs = add_log("긴장감 설계자", "이야기의 긴장감이 어떻게 요동치는지 분석해 볼게요. 독자들이 숨죽이고 읽을 만한 클라이맥스가 어디인지 찾아보겠습니다!")
    
    result = tension_curve_agent.run(
        state.get("split_text"),
        persona=state.get("reader_persona")
    )
    
    # 긴장도 곡선은 보통 curve 리스트를 반환함
    curve_points = len(result.get("curve", []))
    if curve_points > 0:
        logs += add_log("긴장감 설계자", f"전체적인 긴장도 흐름을 {curve_points}개의 포인트로 분석 완료했어요! 글의 완급 조절이 아주 흥미롭네요.")
    else:
        logs += add_log("긴장감 설계자", "긴장도 분석을 마쳤어요. 리포트의 그래프를 통해 이야기의 호흡을 한눈에 확인해 보세요!")
        
    logger.info("긴장감 분석: [END]")
    return {
        "tension_curve_result": result,
        "logs": logs
    }
