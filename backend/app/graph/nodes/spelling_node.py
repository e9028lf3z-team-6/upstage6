# app/graph/nodes/spelling_node.py
from app.agents import SpellingAgent
from app.graph.state import AgentState
from app.observability.langsmith import traceable_timed

spelling_agent = SpellingAgent()

@traceable_timed(name="spelling")
def spelling_node(state: AgentState) -> AgentState:
    text = state["original_text"]
    # SpellingAgent expects a list of strings (sentences/chunks)
    # Simple splitting by newlines for now.
    sentences = [s.strip() for s in text.split("\n") if s.strip()]
    if not sentences:
        sentences = [text]

    result = spelling_agent.run(sentences)

    return {
        "spelling_result": result
    }
