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


def _find_char_range_with_hint(
    quote: str,
    sentence: str,
    hint_start: int | None,
    margin: int = 20
) -> Tuple[int | None, int | None]:
    if not quote or not sentence:
        return None, None
        
    sentence_len = len(sentence)
    
    # 1. Hint 주변 검색 (Proximity Search)
    if hint_start is not None:
        # LLM이 준 위치를 기준으로 앞뒤 margin만큼 범위를 좁혀서 검색
        search_start = max(0, hint_start - margin)
        search_end = min(sentence_len, hint_start + len(quote) + margin)
        
        sub_sentence = sentence[search_start:search_end]
        sub_idx = sub_sentence.find(quote)
        
        if sub_idx != -1:
            final_start = search_start + sub_idx
            return final_start, final_start + len(quote)

    # 2. Hint 실패 시 전체 검색 (Fallback)
    idx = sentence.find(quote)
    if idx != -1:
        return idx, idx + len(quote)
        
    return None, None


def _find_char_range(quote: str, sentence: str) -> Tuple[int | None, int | None]:
    # Deprecated: Use _find_char_range_with_hint instead if possible
    return _find_char_range_with_hint(quote, sentence, None)

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

    # 1. 인덱스가 아예 없는 경우에만 전역 검색 (기존 로직 유지)
    if sentence_index is None or sentence_index >= len(sentences):
        sentence_index = _find_sentence_index(quote, sentences)
        if sentence_index is None and quote_stripped:
            sentence_index = _find_sentence_index(quote_stripped, sentences)
    
    # 2. 인덱스가 유효하지 않으면 포기
    if sentence_index is None or sentence_index >= len(sentences):
        return None

    # 3. [Anchor Locking] 문장 인덱스 고정
    sentence = sentences[sentence_index]
    sentence_len = len(sentence)
    
    # 4. 문장 내에서 Quote 찾기 (Proximity Search 적용)
    final_start, final_end = None, None

    # 4-1. LLM이 준 char offset이 유효하고, 실제 텍스트와 일치하는지 확인
    if char_start is not None and char_end is not None:
        char_start = max(0, min(char_start, sentence_len))
        char_end = max(0, min(char_end, sentence_len))
        if char_end > char_start:
            # 오프셋으로 잘랐을 때 quote와 유사하거나, quote가 없으면 오프셋 신뢰
            sliced = sentence[char_start:char_end]
            if not quote or quote in sliced or sliced in quote:
                final_start, final_end = char_start, char_end

    # 4-2. 오프셋 신뢰 불가 시, 힌트 기반 검색
    if final_start is None:
        if quote:
            s, e = _find_char_range_with_hint(quote, sentence, char_start)
            if s is not None:
                final_start, final_end = s, e
        
        if final_start is None and quote_stripped:
            s, e = _find_char_range_with_hint(quote_stripped, sentence, char_start)
            if s is not None:
                final_start, final_end = s, e

    # 5. [Fallback] 정 못 찾겠으면 문장 전체 하이라이팅 (다른 문장으로 튀는 것보다 낫다)
    if final_start is None:
        final_start, final_end = 0, sentence_len

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
        "char_start": int(final_start),
        "char_end": int(final_end),
        "doc_start": int(doc_start) + int(final_start),
        "doc_end": int(doc_start) + int(final_end),
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
