# app/services/pipeline_runner.py
from app.graph.graph import agent_app
from app.graph.state import AgentState


def run_full_pipeline(
    text: str,
    context: str | None = None,
    debug: bool = False,
) -> dict:
    """
    LangGraph 기반 전체 파이프라인 실행기
    - prod / dev / debug 공용
    """

    # --------------------------------------------------
    # Initial state (entry contract만 만족시키면 충분)
    # --------------------------------------------------
    initial_state: AgentState = {
        "original_text": text,
        "context": context,
    }

    # --------------------------------------------------
    # Run graph
    # --------------------------------------------------
    final_state: AgentState = agent_app.invoke(initial_state)

    # --------------------------------------------------
    # Production output
    # --------------------------------------------------
    if not debug:
        return {
            "final_report": final_state.get("final_report"),
            "decision": (final_state.get("aggregated_result") or {}).get("decision"),
        }

    # --------------------------------------------------
    # Debug / Dev output
    # --------------------------------------------------
    return {
        # core results
        "final_report": final_state.get("final_report"),
        "decision": (final_state.get("aggregated_result") or {}).get("decision"),

        # evaluators
        "tone": final_state.get("tone_result"),
        "logic": final_state.get("logic_result"),
        "trauma": final_state.get("trauma_result"),
        "hate_bias": final_state.get("hate_bias_result"),
        "genre_cliche": final_state.get("genre_cliche_result"),
        "spelling": final_state.get("spelling_result"),

        # persona
        "reader_persona": final_state.get("reader_persona"),
        "persona_feedback": final_state.get("persona_feedback"),

        # aggregate
        "aggregated": final_state.get("aggregated_result"),

        # rewrite
        "rewrite_guidelines": final_state.get("rewrite_guidelines"),
    }
