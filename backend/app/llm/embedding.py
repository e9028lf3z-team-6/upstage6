from typing import List
from app.llm.client import get_upstage_client

EMBEDDING_MODEL = "embedding-query"
# (= solar-embedding-1-large-query)

def embed_text(text: str) -> List[float]:
    client = get_upstage_client()
    res = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return res.data[0].embedding
