# app/graph/nodes/causality_node.py
from app.agents import CausalityEvaluatorAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

causality_agent = CausalityEvaluatorAgent()

@traceable_timed(name="logic")
def causality_node(state: AgentState) -> AgentState:
    logger.info("개연성 분석: [START]")
    logs = add_log("서사 분석가", "이야기의 흐름을 따라가 보며, 독자들이 고개를 갸우뚱할 만한 부분은 없는지 개연성을 살펴볼게요. 긴장되는 순간이네요!")
    
    result = causality_agent.run(
        state.get("split_text"),
        global_summary=state.get("global_summary"),
        persona=state.get("reader_persona")
    )
    
    issue_count = len(result.get("issues", []))
    if issue_count > 0:
        logs += add_log("서사 분석가", f"이야기 중에 살짝 보완이 필요한 지점을 {issue_count}군데 발견했어요. 이 부분을 조금만 더 다듬으면 독자들이 훨씬 더 몰입할 수 있을 것 같아요!")
    else:
        logs += add_log("서사 분석가", "글의 구성이 정말 탄탄해요! 인과관계가 물 흐르듯 자연스러워서 독자들이 이야기 속에 푹 빠져들 것 같습니다.")
        
    logger.info("개연성 분석: [END]")
    return {
        "logic_result": result,
        "logs": logs
    }

