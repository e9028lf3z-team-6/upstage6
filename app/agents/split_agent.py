from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.llm.embedding import embed_text

class SplitAgent(BaseAgent):
    name = "split-agent"

    def run(self, input_data: str) -> dict:
        split_prompt = f"""
        다음 원고를 평가 가능한 요소로 분리하라.
        - 말투
        - 인과관계
        - 장르
        - 부적절한 표현

        원고:
        {input_data}
        """

        split_text = chat(split_prompt)
        embedding = embed_text(input_data)

        return {
            "split_text": split_text,
            "embedding_dim": len(embedding),
        }
