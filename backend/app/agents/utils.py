import json
from typing import Any, List, Tuple


def extract_split_payload(split_payload: Any) -> Tuple[str, List[str]]:
    summary = ""
    sentences: List[str] = []

    if isinstance(split_payload, dict):
        summary = str(split_payload.get("split_text") or "")
        raw_sentences = split_payload.get("split_sentences")
        if isinstance(raw_sentences, list):
            sentences = [str(s) for s in raw_sentences]
    elif isinstance(split_payload, list):
        sentences = [str(s) for s in split_payload]
    elif isinstance(split_payload, str):
        summary = split_payload

    return summary, sentences


def format_split_payload(split_payload: Any) -> str:
    _, sentences = extract_split_payload(split_payload)
    parts: List[str] = []
    if sentences:
        parts.append("[문장 목록 JSON 배열 (index가 sentence_index)]")
        parts.append(json.dumps(sentences, ensure_ascii=False))
    return "\n".join(parts)
