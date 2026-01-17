# app/graph/nodes/reader_persona_node.py
from app.agents import ReaderPersonaAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

reader_persona_agent = ReaderPersonaAgent()

@traceable_timed(name="reader_persona")
def reader_persona_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 1/6 - 분석 시작 및 페르소나 설정 중...")
    context = state.get("context")
    
    try:
        result = reader_persona_agent.run(context)
        # Ensure result is a dict
        if not isinstance(result, dict):
            logger.warning(f"reader_persona_agent returned non-dict: {type(result)}")
            result = {"persona": {"name": "기본 독자", "role": "일반인", "expectations": ["일반적인 가독성"]}}
    except Exception as e:
        logger.error(f"Error in reader_persona_node: {e}")
        result = {"persona": {"name": "기본 독자", "role": "일반인", "expectations": ["일반적인 가독성"]}, "error": str(e)}

    return {
        "reader_persona": result
    }
