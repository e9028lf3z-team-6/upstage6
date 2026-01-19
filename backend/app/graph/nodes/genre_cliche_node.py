from app.agents import GenreClicheAgent
from app.graph.state import AgentState
from app.graph.nodes.utils import add_log
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

genre_cliche_agent = GenreClicheAgent()

@traceable_timed(name="genre_cliche")
def genre_cliche_node(state: AgentState) -> AgentState:
    logger.info("클리셰 분석: [START]")
    logs = add_log("장르 전문가", "이 장르의 매력을 얼마나 잘 살렸는지, 혹시 너무 뻔한 클리셰는 없는지 제가 매의 눈으로 찾아볼게요!")
    
    result = genre_cliche_agent.run(
        state.get("split_text"),
        global_summary=state.get("global_summary"),
        persona=state.get("reader_persona")
    )
    
    issue_count = len(result.get("issues", []))
    if issue_count > 0:
        logs += add_log("장르 전문가", f"장르적 재미를 더하기 위해 {issue_count}가지 정도 제안하고 싶은 게 있어요. 클리셰를 비틀면 더 멋진 글이 될 거예요!")
    else:
        logs += add_log("장르 전문가", "클리셰를 아주 신선하게 활용하셨네요! 장르의 맛을 살리면서도 독창성이 돋보이는 구성입니다.")
        
    logger.info("클리셰 분석: [END]")
    return {
        "genre_cliche_result": result,
        "logs": logs
    }
