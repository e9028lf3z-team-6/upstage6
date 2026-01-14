from app.agents.tools.summary_agent import SummaryAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)
summary_agent = SummaryAgent()

@traceable_timed(name="summarize")
def summary_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 2.5/6 - 전체 맥락 요약 중...")
    
    # original_text 또는 split_text를 기반으로 요약
    text = state.get("original_text") or ""
    summary = summary_agent.run(text)
    
    return {
        "global_summary": summary
    }
