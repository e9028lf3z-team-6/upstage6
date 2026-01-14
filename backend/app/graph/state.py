# app/graph/state.py
from typing import TypedDict, Optional, Dict, Any, List, Union


class AgentState(TypedDict, total=False):
    # entry
    original_text: str
    context: Optional[str]

    # preprocessing
    split_text: Optional[Union[List[str], Dict[str, Any], str]]
    split_sentences: Optional[List[str]]
    split_map: Optional[List[Dict[str, Any]]]
    global_summary: Optional[str]

    # persona
    reader_persona: Optional[Dict[str, Any]]
    persona_feedback: Optional[Dict[str, Any]]

    # evaluators
    tone_result: Optional[Dict[str, Any]]
    logic_result: Optional[Dict[str, Any]]
    trauma_result: Optional[Dict[str, Any]]
    hate_bias_result: Optional[Dict[str, Any]]
    genre_cliche_result: Optional[Dict[str, Any]]
    spelling_result: Optional[Dict[str, Any]]
    tension_curve_result: Optional[Dict[str, Any]]

    # aggregate
    aggregated_result: Optional[Dict[str, Any]]
    # expected keys:
    # {
    #   "decision": "rewrite" | "report",
    #   "has_issues": bool,
    #   ...
    # }

    # rewrite / output
    rewrite_guidelines: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]

    # evaluators
    qa_scores: Optional[Dict[str, Any]]
    final_metric: Optional[Dict[str, Any]]
