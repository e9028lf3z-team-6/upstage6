# app/graph/nodes/spelling_node.py
from app.agents import SpellingAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

spelling_agent = SpellingAgent()

@traceable_timed(name="spelling")
def spelling_node(state: AgentState) -> AgentState:
    logger.info("맞춤법 검사: [START]")
    logs = add_log("맞춤법 전문가", "안녕하세요! 저는 맞춤법 요정이에요. 작가님이 집필에 집중하시느라 미처 챙기지 못한 오타나 띄어쓰기들을 제가 예쁘게 찾아볼게요.")
    
    result = spelling_agent.run(state.get("split_text"))
    
    issue_count = len(result.get("issues", []))
    if issue_count > 0:
        logs += add_log("맞춤법 전문가", f"작가님, 제가 읽어보니 수정하면 더 완벽해질 부분이 {issue_count}군데 정도 보여요! 리포트에 꼼꼼히 적어두었으니 나중에 확인해 보세요.")
    else:
        logs += add_log("맞춤법 전문가", "우와, 정말 대단하세요! 맞춤법이 정말 완벽해서 제가 더 이상 손댈 곳이 없네요. 최고예요! 👍")
        
    logger.info("맞춤법 검사: [END]")
    return {
        "spelling_result": result,
        "logs": logs
    }
