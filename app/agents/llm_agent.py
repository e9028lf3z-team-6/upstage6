from app.agents.base import BaseAgent
from app.llm.chat import chat

class LLMAgent(BaseAgent):
    name = "llm-agent"

    def run(self, input_data: str) -> str:
        return chat(
            prompt=input_data,
            system="You are a helpful evaluation agent."
        )
