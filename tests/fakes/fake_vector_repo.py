from typing import List, Dict, Any
from app.repository.vector_repo import VectorRepository


class FakeVectorRepository(VectorRepository):
    def __init__(self):
        self._docs = []

    def add_documents(self, documents, embeddings=None, metadatas=None, ids=None):
        self._docs.extend(documents)

    def query(self, query_embeddings=None, n_results=5, include=None):
        return {
            "documents": [self._docs[:n_results]],
            "metadatas": [[{} for _ in self._docs[:n_results]]],
            "distances": [[0.1 for _ in self._docs[:n_results]]],
        }

    def delete_documents(self, ids):
        pass

    def get_collection_info(self):
        return {"count": len(self._docs)}
