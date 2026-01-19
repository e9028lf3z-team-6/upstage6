# app/graph/nodes/reader_persona_node.py
from app.agents import ReaderPersonaAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

reader_persona_agent = ReaderPersonaAgent()

@traceable_timed(name="reader_persona")
def reader_persona_node(state: AgentState) -> AgentState:
    logger.info("페르소나 설정: [START]")
    
    # Context 정제 및 본문 프리뷰 추가
    raw_context = state.get("context")
    clean_context = {}
    
    # 1. 메타데이터 정제 (기술적 필드 제거)
    if raw_context:
        try:
            import json
            if isinstance(raw_context, str):
                meta = json.loads(raw_context)
            else:
                meta = raw_context
            
            if isinstance(meta, dict):
                clean_context = {
                    k: v for k, v in meta.items() 
                    if k not in ["source", "upstage_raw_keys", "upstage_error", "file_type", "issue_counts_json", "result_json"]
                }
        except Exception as e:
            logger.warning(f"Context parsing failed: {e}")
            clean_context = {"raw": str(raw_context)}

    # 2. 본문 내용 반영 (제목/서문 등)
    original_text = state.get("original_text", "")
    preview_text = original_text[:3000] if original_text else ""

    # 3. 에이전트 입력 구성
    agent_input = {
        "meta": clean_context,
        "text_preview": preview_text
    }

    result = reader_persona_agent.run(agent_input)
    logger.info("페르소나 설정: [END]")
    return {
        "reader_persona": result
    }
