# app/graph/nodes/split_node.py
from app.agents.tools.split import Splitter
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed
import logging

logger = logging.getLogger(__name__)
splitter = Splitter()

@traceable_timed(name="split")
def split_node(state: AgentState) -> AgentState:
    logger.info("텍스트 분할: [START]")
    result = splitter.run(state["original_text"])
    logger.info("텍스트 분할: [END]")

    return {
        "split_text": result,
        "split_sentences": result.get("split_sentences"),
        "split_map": result.get("split_map"),
    }
