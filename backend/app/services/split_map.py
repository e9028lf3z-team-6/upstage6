import re
from typing import Dict, List, Tuple


_SENTENCE_PATTERN = re.compile(r".*?(?:[.!?]|\n|$)", re.S)


def split_with_map(text: str) -> Tuple[List[str], List[Dict[str, int | str]]]:
    sentences: List[str] = []
    split_map: List[Dict[str, int | str]] = []

    for match in _SENTENCE_PATTERN.finditer(text):
        segment = match.group()
        if not segment or not segment.strip():
            continue
        leading = len(segment) - len(segment.lstrip())
        trailing = len(segment) - len(segment.rstrip())
        doc_start = match.start() + leading
        doc_end = match.end() - trailing
        if doc_end <= doc_start:
            continue
        sentence = text[doc_start:doc_end]
        sentence_index = len(sentences)
        sentences.append(sentence)
        split_map.append(
            {
                "sentence_index": sentence_index,
                "doc_start": doc_start,
                "doc_end": doc_end,
                "text": sentence,
            }
        )

    if not sentences:
        stripped = text.strip()
        if stripped:
            start = text.find(stripped)
            end = start + len(stripped)
            sentences = [stripped]
            split_map = [
                {
                    "sentence_index": 0,
                    "doc_start": start,
                    "doc_end": end,
                    "text": stripped,
                }
            ]

    return sentences, split_map


def build_split_payload(
    text: str,
    summary: str | None = None,
    embedding_dim: int | None = None,
) -> Dict[str, object]:
    sentences, split_map = split_with_map(text)
    payload: Dict[str, object] = {
        "split_text": summary or "",
        "split_sentences": sentences,
        "split_map": split_map,
    }
    if embedding_dim is not None:
        payload["embedding_dim"] = embedding_dim
    return payload
