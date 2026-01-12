from typing import TypedDict, Any, List

from langgraph.graph import StateGraph, END

from app.agents.tools.split_agent import SplitAgent
from app.agents.tools.tone_agent import ToneEvaluatorAgent
from app.agents.tools.causality_agent import CausalityEvaluatorAgent
from app.agents.tools.llm_aggregator import IssueBasedAggregatorAgent, AggregateResult


class LangGraphState(TypedDict):
    text: str
    split: dict | None
    tone: dict | None
    logic: dict | None
    aggregate: dict | None
    errors: List[str]


split_agent = SplitAgent()
tone_agent = ToneEvaluatorAgent()
logic_agent = CausalityEvaluatorAgent()
aggregator_agent = IssueBasedAggregatorAgent()


def _append_error(state: LangGraphState, message: str) -> List[str]:
    return [*state.get("errors", []), message]


def split_node(state: LangGraphState) -> dict:
    try:
        split_result = split_agent.run(state["text"])
    except Exception as exc:
        split_result = {"split_text": [state["text"]]}
        return {
            "split": split_result,
            "errors": _append_error(state, f"split_agent failed: {exc}"),
        }

    return {"split": split_result}


def tone_node(state: LangGraphState) -> dict:
    split_text = (state.get("split") or {}).get("split_text", state["text"])
    try:
        tone_result = tone_agent.run(split_text)
    except Exception as exc:
        tone_result = {"issues": [], "error": str(exc)}
        return {
            "tone": tone_result,
            "errors": _append_error(state, f"tone_agent failed: {exc}"),
        }

    return {"tone": tone_result}


def logic_node(state: LangGraphState) -> dict:
    split_text = (state.get("split") or {}).get("split_text", state["text"])
    try:
        logic_result = logic_agent.run(split_text=split_text)
    except Exception as exc:
        logic_result = {"issues": [], "error": str(exc)}
        return {
            "logic": logic_result,
            "errors": _append_error(state, f"logic_agent failed: {exc}"),
        }

    return {"logic": logic_result}


def aggregate_node(state: LangGraphState) -> dict:
    tone_issues = (state.get("tone") or {}).get("issues", [])
    logic_issues = (state.get("logic") or {}).get("issues", [])

    try:
        aggregate = aggregator_agent.run(
            tone_issues=tone_issues,
            logic_issues=logic_issues,
        )
        aggregate_result: dict[str, Any] = aggregate.dict()
    except Exception as exc:
        aggregate = AggregateResult(
            decision="pass",
            problem_types=[],
            primary_issue=None,
            rationale={"error": str(exc)},
        )
        aggregate_result = aggregate.dict()
        return {
            "aggregate": aggregate_result,
            "errors": _append_error(state, f"aggregator failed: {exc}"),
        }

    return {"aggregate": aggregate_result}


def build_graph():
    graph = StateGraph(LangGraphState)
    graph.add_node("split", split_node)
    graph.add_node("tone", tone_node)
    graph.add_node("logic", logic_node)
    graph.add_node("aggregate", aggregate_node)

    graph.set_entry_point("split")
    graph.add_edge("split", "tone")
    graph.add_edge("tone", "logic")
    graph.add_edge("logic", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()


def run_langgraph_pipeline(text: str, *, debug: bool = False) -> dict:
    graph = build_graph()
    initial_state: LangGraphState = {
        "text": text,
        "split": None,
        "tone": None,
        "logic": None,
        "aggregate": None,
        "errors": [],
    }
    result = graph.invoke(initial_state)

    output = {
        "split": result.get("split"),
        "tone": result.get("tone"),
        "causality": result.get("logic"),
        "aggregate": result.get("aggregate"),
    }

    if debug:
        output["debug"] = {"errors": result.get("errors", [])}

    return output
