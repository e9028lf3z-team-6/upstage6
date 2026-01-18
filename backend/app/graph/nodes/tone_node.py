from app.agents import ToneEvaluatorAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

tone_agent = ToneEvaluatorAgent()

@traceable_timed(name="tone")
def tone_node(state: AgentState) -> AgentState:
    logger.info("톤앤매너 분석: [START]")
    logs = add_log("문체 전문가", "글의 분위기와 말투가 독자들에게 어떻게 전달될지 분석해 볼게요. 펜을 든 작가님의 마음을 느껴보겠습니다.")
    
    result = tone_agent.run(
        state.get("split_text"),
        global_summary=state.get("global_summary"),
        persona=state.get("reader_persona")
    )
    
    issue_count = len(result.get("issues", []))
    if issue_count > 0:
        logs += add_log("문체 전문가", f"작가님, 글의 톤을 조금 더 일관되게 다듬으면 좋을 지점을 {issue_count}군데 정도 찾았어요. 리포트를 참고해 주세요!")
    else:
        logs += add_log("문체 전문가", "와! 문체와 톤앤매너가 정말 훌륭해요. 작가님만의 색깔이 잘 묻어나는 매력적인 글이네요.")
        
    logger.info("톤앤매너 분석: [END]")
    return {
        "tone_result": result,
        "logs": logs
    }
