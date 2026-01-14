from typing import Any, Dict, List, Tuple


_DEFAULT_SEVERITY = {
    "tone": "medium",
    "logic": "medium",
    "trauma": "high",
    "hate_bias": "high",
    "genre_cliche": "low",
    "spelling": "low",
    "tension": "medium",
}


def _safe_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _find_sentence_index(quote: str, sentences: List[str]) -> int | None:
    if not quote:
        return None
    for idx, sentence in enumerate(sentences):
        if quote in sentence:
            return idx
    return None


def _find_char_range(quote: str, sentence: str) -> Tuple[int | None, int | None]:
    if not quote or not sentence:
        return None, None
    start = sentence.find(quote)
    if start == -1:
        return None, None
    return start, start + len(quote)

def _strip_markup(quote: str) -> str:
    if not quote:
        return ""
    cleaned = quote.replace("**", "").replace("__", "").replace("`", "")
    return cleaned.strip()


def _build_location(
    issue: dict,
    sentences: List[str],
    split_map: List[Dict[str, Any]],
) -> Dict[str, int] | None:
    location_payload = issue.get("location") if isinstance(issue.get("location"), dict) else {}
    sentence_index = location_payload.get("sentence_index", issue.get("sentence_index"))
    char_start = location_payload.get("char_start", issue.get("char_start"))
    char_end = location_payload.get("char_end", issue.get("char_end"))
    quote_raw = issue.get("quote") or issue.get("original") or ""
    quote_stripped = _strip_markup(quote_raw)
    quote = quote_raw or ""

    sentence_index = _coerce_int(sentence_index)
    char_start = _coerce_int(char_start)
    char_end = _coerce_int(char_end)

    if sentence_index is None or sentence_index >= len(sentences):
        sentence_index = _find_sentence_index(quote, sentences)
        if sentence_index is None and quote_stripped:
            sentence_index = _find_sentence_index(quote_stripped, sentences)
    if sentence_index is None or sentence_index >= len(sentences):
        return None

    sentence = sentences[sentence_index]
    if quote and quote not in sentence:
        matches = [i for i, s in enumerate(sentences) if quote in s]
        if matches:
            sentence_index = min(matches, key=lambda i: abs(i - sentence_index))
            sentence = sentences[sentence_index]
    if quote_stripped and quote not in sentence and quote_stripped in sentence:
        quote = quote_stripped
    sentence_len = len(sentence)

    if char_start is not None and char_end is not None:
        char_start = max(0, min(char_start, sentence_len))
        char_end = max(0, min(char_end, sentence_len))
        if char_end <= char_start:
            char_start = None
            char_end = None
        elif quote and sentence[char_start:char_end] != quote:
            start, end = _find_char_range(quote, sentence)
            if (start is None or end is None) and quote_stripped:
                start, end = _find_char_range(quote_stripped, sentence)
            if start is not None and end is not None:
                char_start, char_end = start, end

    if char_start is None or char_end is None:
        start, end = _find_char_range(quote, sentence)
        if (start is None or end is None) and quote_stripped:
            start, end = _find_char_range(quote_stripped, sentence)
        if start is None or end is None:
            start, end = 0, sentence_len
        char_start, char_end = start, end

    if sentence_index >= len(split_map):
        return None
    if not isinstance(split_map[sentence_index], dict):
        return None
    doc_start = split_map[sentence_index].get("doc_start")
    doc_end = split_map[sentence_index].get("doc_end")
    if doc_start is None or doc_end is None:
        return None

    return {
        "sentence_index": int(sentence_index),
        "char_start": int(char_start),
        "char_end": int(char_end),
        "doc_start": int(doc_start) + int(char_start),
        "doc_end": int(doc_start) + int(char_end),
    }


def _normalize_issue(
    agent: str,
    raw_issue: dict,
    sentences: List[str],
    split_map: List[Dict[str, Any]],
    index: int,
) -> Dict[str, Any] | None:
    issue_type = (
        raw_issue.get("issue_type")
        or raw_issue.get("type")
        or raw_issue.get("error_type")
        or raw_issue.get("trigger_type")
        or raw_issue.get("bias_type")
        or raw_issue.get("issue")
        or "unspecified"
    )

    severity = raw_issue.get("severity") or _DEFAULT_SEVERITY.get(agent, "medium")
    quote = raw_issue.get("quote") or raw_issue.get("original") or raw_issue.get("evidence") or ""
    reason = (
        raw_issue.get("reason")
        or raw_issue.get("description")
        or raw_issue.get("problem")
        or raw_issue.get("reader_impact")
        or raw_issue.get("pattern")
        or ""
    )
    suggestion = raw_issue.get("suggestion")
    confidence = _safe_number(raw_issue.get("confidence"))

    location = _build_location(raw_issue, sentences, split_map)

    if location and not quote:
        quote = sentences[location["sentence_index"]][
            location["char_start"] : location["char_end"]
        ]

    return {
        "id": f"{agent}-{index:04d}",
        "agent": agent,
        "issue_type": str(issue_type),
        "severity": str(severity),
        "confidence": confidence,
        "location": location,
        "quote": quote,
        "reason": reason,
        "suggestion": suggestion,
    }


def normalize_issues(outputs: dict, split_payload: dict | None) -> Tuple[List[dict], List[dict]]:
    split_payload = split_payload or {}
    sentences = split_payload.get("split_sentences")
    if not isinstance(sentences, list):
        sentences = []
    split_map = split_payload.get("split_map")
    if not isinstance(split_map, list):
        split_map = []

    normalized: List[dict] = []
    highlight_items: List[dict] = []

    def _collect(agent_key: str, raw_result: dict, issues_key: str = "issues"):
        issues = raw_result.get(issues_key) or []
        for idx, raw_issue in enumerate(issues):
            if not isinstance(raw_issue, dict):
                continue
            normalized_issue = _normalize_issue(
                agent_key, raw_issue, sentences, split_map, len(normalized)
            )
            if not normalized_issue:
                continue
            normalized.append(normalized_issue)

    _collect("tone", outputs.get("tone") or {})
    _collect("logic", outputs.get("logic") or outputs.get("causality") or {})
    _collect("trauma", outputs.get("trauma") or {})
    _collect("hate_bias", outputs.get("hate_bias") or {})
    _collect("genre_cliche", outputs.get("genre_cliche") or {})
    _collect("spelling", outputs.get("spelling") or {})
    tension = outputs.get("tension_curve") or {}
    _collect("tension", tension)
    _collect("tension", tension, issues_key="anomalies")

    for issue in normalized:
        location = issue.get("location") or {}
        doc_start = location.get("doc_start")
        doc_end = location.get("doc_end")
        if doc_start is None or doc_end is None:
            continue
        highlight_items.append(
            {
                "agent": issue.get("agent"),
                "severity": issue.get("severity"),
                "doc_start": doc_start,
                "doc_end": doc_end,
                "label": issue.get("issue_type"),
                "reason": issue.get("reason") or issue.get("issue_type"),
            }
        )

    return normalized, highlight_items
