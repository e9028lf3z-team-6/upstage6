# app/graph/nodes/spelling_node.py
from app.agents import SpellingAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

spelling_agent = SpellingAgent()

@traceable_timed(name="spelling")
def spelling_node(state: AgentState) -> AgentState:
    split_text = state.get("split_text")

    # split_text 구조 방어
    sentences = []
    if isinstance(split_text, dict):
        sentences = split_text.get("split_text", [])
    elif isinstance(split_text, list):
        sentences = split_text

    result = spelling_agent.run(sentences)

    return {
        "spelling_result": result
    }
