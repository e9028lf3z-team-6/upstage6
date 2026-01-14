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
    result = reader_persona_agent.run(state["context"])
    return {
        "reader_persona": result
    }
