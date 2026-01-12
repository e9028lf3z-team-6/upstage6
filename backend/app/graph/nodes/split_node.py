# app/graph/nodes/split_node.py
from app.agents import SplitAgent
from app.graph.state import AgentState

split_agent = SplitAgent()

def split_node(state: AgentState) -> AgentState:
    result = split_agent.run(state["original_text"])

    return {
        **state,
        "split_text": result
    }
