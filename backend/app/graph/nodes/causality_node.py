# app/graph/nodes/causality_node.py
from app.agents import CausalityEvaluatorAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)

causality_agent = CausalityEvaluatorAgent()

@traceable_timed(name="logic")
def causality_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 3/6 - [Causality] 개연성 분석 시작...")
    
    split_text = state.get("split_text")
    if not split_text or (isinstance(split_text, dict) and not split_text.get("split_sentences")):
        logger.warning("causality_node: No text to analyze.")
        return {"logic_result": {"issues": [], "score": 10, "note": "분석할 텍스트가 없습니다."}}

    reader_context = None
    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona", {})
        reader_context = {
            "knowledge_level": persona.get("knowledge_level", "중급")
        }

    try:
        result = causality_agent.run(
            split_text,
            reader_context=reader_context,
            global_summary=state.get("global_summary")
        )
    except Exception as e:
        logger.error(f"Error in causality_node: {e}")
        result = {"issues": [], "score": 0, "error": str(e)}

    return {
        "logic_result": result
    }

