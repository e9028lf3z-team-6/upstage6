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
    reader_context = None

    if state.get("reader_persona"):
        persona = state["reader_persona"].get("persona", {})
        reader_context = {
            "knowledge_level": persona.get("knowledge_level", "중급")
        }

    result = causality_agent.run(
        state.get("split_text"),
        reader_context=reader_context,
        global_summary=state.get("global_summary")
    )

    return {
        "logic_result": result
    }

