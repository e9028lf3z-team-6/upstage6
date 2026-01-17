import json
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState

# entry / context
from app.graph.nodes.reader_persona_node import reader_persona_node
from app.graph.nodes.split_node import split_node
from app.graph.nodes.summary_node import summary_node
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
graph.add_node("summary", summary_node)
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

# split → summary
graph.add_edge("split", "summary")

# split → persona_feedback (Wait, persona_feedback needs summary? Original was summary->persona_feedback)
# Re-checking original: graph.add_edge("summary", "persona_feedback")
# But persona_feedback is also an evaluator-like node.
# Let's keep it connected to summary for now, but maybe it should be parallel too?
# Current logic: Summary is context for persona feedback.
graph.add_edge("summary", "persona_feedback")

# --------------------------------------------------
# Routing Logic (Selective Execution)
# --------------------------------------------------
def route_to_evaluators(state: AgentState):
    """
    meta_json의 settings.selected_agents를 확인하여
    실행할 평가 에이전트 노드들의 리스트를 반환합니다.
    """
    all_evaluators = [
        "tone", "logic", "trauma", "hate_bias", 
        "genre_cliche", "spelling", "tension_curve"
    ]
    
    context_str = state.get("context")
    if not context_str:
        return all_evaluators # Default: Run all if no settings

    try:
        if isinstance(context_str, dict):
            meta = context_str
        else:
            meta = json.loads(context_str)

        settings = meta.get("settings", {})
        selected = settings.get("selected_agents")
        
        if not selected or not isinstance(selected, list):
            return all_evaluators # Default: Run all if selection is missing/empty
            
        # Filter valid nodes only
        to_run = [agent for agent in selected if agent in all_evaluators]
        
        if not to_run:
            return all_evaluators # Fallback: Run all if filter resulted in empty list
            
        return to_run
        
    except json.JSONDecodeError:
        return all_evaluators

# --------------------------------------------------
# Evaluators (parallel fan-out)
# --------------------------------------------------

# summary -> [Selected Evaluators]
graph.add_conditional_edges(
    "summary",
    route_to_evaluators,
    # Map is not strictly needed if function returns node names directly, 
    # but explicit mapping is good practice in LangGraph.
    {
        "tone": "tone",
        "logic": "logic",
        "trauma": "trauma",
        "hate_bias": "hate_bias",
        "genre_cliche": "genre_cliche",
        "spelling": "spelling",
        "tension_curve": "tension_curve"
    }
)

# Evaluators -> Aggregate
for node in [
    "tone",
    "logic",
    "trauma",
    "hate_bias",
    "genre_cliche",
    "spelling",
    "tension_curve",
]:
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
