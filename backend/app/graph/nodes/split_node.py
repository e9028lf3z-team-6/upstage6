# app/graph/nodes/split_node.py
from app.agents import SplitAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)
split_agent = SplitAgent()

@traceable_timed(name="split")
def split_node(state: AgentState) -> AgentState:
    logger.info("[DEBUG] split_node: Starting.")
    result = split_agent.run(state["original_text"])
    logger.info("[DEBUG] split_node: Finished.")

    return {
        "split_text": result,
        "split_sentences": result.get("split_sentences"),
        "split_map": result.get("split_map"),
    }
