# app/graph/nodes/split_node.py
from app.agents import SplitAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

split_agent = SplitAgent()

@traceable_timed(name="split")
def split_node(state: AgentState) -> AgentState:
    result = split_agent.run(state["original_text"])

    return {
        "split_text": result,
        "split_sentences": result.get("split_sentences"),
        "split_map": result.get("split_map"),
    }
