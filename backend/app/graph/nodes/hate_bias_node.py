from app.agents import HateBiasAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

hate_bias_agent = HateBiasAgent()

@traceable_timed(name="hate_bias")
def hate_bias_node(state: AgentState) -> AgentState:
    logger.info("혐오/편향 분석: [START]")
    logs = add_log("윤리 감시자", "사회적 편견이나 혐오 표현이 숨어있지는 않은지 꼼꼼히 점검해 보겠습니다. 모두가 존중받는 이야기를 위해!")
    
    result = hate_bias_agent.run(
        state.get("split_text")
    )
    
    issue_count = len(result.get("issues", []))
    if issue_count > 0:
        logs += add_log("윤리 감시자", f"더 따뜻한 시선으로 다듬어지면 좋을 부분이 {issue_count}군데 있어요. 작가님의 진심이 오해 없이 전달되도록 도와드릴게요.")
    else:
        logs += add_log("윤리 감시자", "완벽해요! 누군가를 차별하거나 배제하지 않는 성숙하고 건강한 가치관이 돋보이는 글입니다.")
        
    logger.info("혐오/편향 분석: [END]")
    return {
        "hate_bias_result": result,
        "logs": logs
    }
