from langgraph.graph import StateGraph, END
from app.graph.state import AgentState

# entry / context
from app.graph.nodes.reader_persona_node import reader_persona_node
from app.graph.nodes.split_node import split_node
from app.graph.nodes.persona_feedback_node import persona_feedback_node

# evaluators
from app.graph.nodes.tone_node import tone_node
from app.graph.nodes.causality_node import causality_node as logic_node
from app.graph.nodes.trauma_node import trauma_node
from app.graph.nodes.hate_bias_node import hate_bias_node
from app.graph.nodes.genre_cliche_node import genre_cliche_node
from app.graph.nodes.spelling_node import spelling_node
from app.graph.nodes.tension_curve_node import tension_curve_node
from app.graph.nodes.qa_scores_node import qa_scores_node

# core decision / output
from app.graph.nodes.aggregate_node import aggregate_node
from app.graph.nodes.rewrite_node import rewrite_node
from app.graph.nodes.report_node import report_node


# --------------------------------------------------
# Graph definition
# --------------------------------------------------
graph = StateGraph(AgentState)

# --------------------------------------------------
# Nodes
# --------------------------------------------------

# entry / context
graph.add_node("reader_persona", reader_persona_node)
graph.add_node("split", split_node)
graph.add_node("persona_feedback", persona_feedback_node)

# evaluators (parallel)
graph.add_node("tone", tone_node)
graph.add_node("logic", logic_node)
graph.add_node("trauma", trauma_node)
graph.add_node("hate_bias", hate_bias_node)
graph.add_node("genre_cliche", genre_cliche_node)
graph.add_node("spelling", spelling_node)
graph.add_node("tension_curve", tension_curve_node)

# decision / output
graph.add_node("aggregate", aggregate_node)
graph.add_node("rewrite", rewrite_node)
graph.add_node("report", report_node)
graph.add_node("qa_scores", qa_scores_node)

# --------------------------------------------------
# Entry point
# --------------------------------------------------
# reader_persona는 context만 필요하므로 entry로 둔다
graph.set_entry_point("reader_persona")

# --------------------------------------------------
# Context / preprocessing flow
# --------------------------------------------------

# context → split
graph.add_edge("reader_persona", "split")

# persona_feedback는 split 결과가 필요하므로 split 이후에만 실행
graph.add_edge("split", "persona_feedback")

# --------------------------------------------------
# Evaluators (parallel fan-out)
# --------------------------------------------------
for node in [
    "tone",
    "logic",
    "trauma",
    "hate_bias",
    "genre_cliche",
    "spelling",
    "tension_curve",
]:
    graph.add_edge("split", node)
    graph.add_edge(node, "aggregate")

# persona feedback도 aggregate로
graph.add_edge("persona_feedback", "aggregate")

# --------------------------------------------------
# Decision routing
# --------------------------------------------------
def route_after_aggregate(state: AgentState):
    decision = (state.get("aggregated_result") or {}).get("decision")
    return "rewrite" if decision == "rewrite" else "report"


graph.add_conditional_edges(
    "aggregate",
    route_after_aggregate,
    {
        "rewrite": "rewrite",
        "report": "report",
    },
)

# --------------------------------------------------
# Finalization
# --------------------------------------------------
graph.add_edge("rewrite", "report")
graph.add_edge("report", "qa_scores")
graph.add_edge("qa_scores", END)

# --------------------------------------------------
# Compile
# --------------------------------------------------
agent_app = graph.compile()
