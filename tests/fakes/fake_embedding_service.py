class FakeEmbeddingService:
    def create_embeddings(self, texts):
        return [[0.1] * 10 for _ in texts]

    def create_embedding(self, text):
        return [0.1] * 10
