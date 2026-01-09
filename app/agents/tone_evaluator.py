import json
import re
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.schemas.score import ToneScore

class ToneEvaluatorAgent(BaseAgent):
    name = "tone-evaluator"

    def run(self, split_text: str) -> ToneScore:
        system = """
        You are a strict JSON generator.
        You MUST output valid JSON only.
        Do NOT include explanations, markdown, or text.
        """

        prompt = f"""
        Evaluate the tone of the following text.
        Fill all fields with numbers between 0 and 1.

        Output format:
        {{
          "clarity": number,
          "neutrality": number,
          "politeness": number
        }}

        Text:
        {split_text}
        """

        response = chat(prompt, system=system)

        data = self._safe_json_load(response)
        return ToneScore(**data)

    def _safe_json_load(self, text: str) -> dict:
        """
        LLM 출력에서 JSON만 안전하게 추출
        """
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"LLM did not return JSON: {text}")

        return json.loads(match.group())
