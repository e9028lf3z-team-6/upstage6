from typing import List
from app.llm.client import get_upstage_client
from app.observability.langsmith import create_llm_run

EMBEDDING_MODEL = "embedding-query"
# (= solar-embedding-1-large-query)

def embed_text(text: str) -> List[float]:
    client = get_upstage_client()
    res = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    usage = getattr(res, "usage", None)
    usage_payload = None
    if usage:
        usage_payload = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }
    create_llm_run(
        name="embeddings",
        provider="upstage",
        model=EMBEDDING_MODEL,
        inputs={"input": text},
        outputs={"embedding_dim": len(res.data[0].embedding)},
        usage=usage_payload,
    )
    return res.data[0].embedding
