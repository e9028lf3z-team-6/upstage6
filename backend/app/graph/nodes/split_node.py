# app/graph/nodes/split_node.py
from app.agents import SplitAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)
split_agent = SplitAgent()

@traceable_timed(name="split")
def split_node(state: AgentState) -> AgentState:
    logger.info("[PROGRESS] 2/6 - 텍스트 분할 및 구조화 (Split) 수행 중...")
    text = state.get("original_text", "")
    
    try:
        # Input validation for empty text
        if not text or not text.strip():
            logger.warning("split_node: original_text is empty or whitespace.")
            fallback = {"split_sentences": [], "split_map": []}
            return {
                "split_text": fallback,
                "split_sentences": [],
                "split_map": [],
            }

        result = split_agent.run(text)
        
        if not isinstance(result, dict):
            logger.warning(f"split_agent returned non-dict: {type(result)}")
            result = {"split_sentences": [text], "split_map": [{"text": text, "index": 0}]}
            
    except Exception as e:
        logger.error(f"Error in split_node: {e}")
        # Robust fallback: treat the whole text as one segment
        result = {
            "split_sentences": [text] if text else [],
            "split_map": [{"text": text, "index": 0}] if text else [],
            "error": str(e)
        }

    logger.info("[DEBUG] split_node: Finished.")

    return {
        "split_text": result,
        "split_sentences": result.get("split_sentences", []),
        "split_map": result.get("split_map", []),
    }
