from app.agents.base import BaseAgent
from app.llm.chat import chat


class SpellingAgent(BaseAgent):
    """
    맞춤법/표기 오류 탐지 에이전트

    역할:
    - 문장 단위로 분리된 텍스트를 입력으로 받음
    - 맞춤법, 띄어쓰기, 조사, 비표준 표현만 탐지
    - 평가, 점수, 수정 제안은 하지 않음
    """

    name = "spelling-agent"

    def run(self, split_text: list[str]) -> dict:
        system = """
너는 맞춤법 오류 탐지 전용 시스템이다.
반드시 JSON만 출력한다.
설명, 문장, 마크다운, 추가 텍스트 출력 금지.
"""

        prompt = f"""
입력은 문장 배열이다.
index는 0부터 시작한다.

역할:
- 맞춤법, 띄어쓰기, 조사, 비표준 표현만 탐지
- 의미, 논리, 말투 평가는 하지 말 것
- 수정된 문장 제시 금지

출력 형식(JSON):
{{
  "issues": [
    {{
      "location": {{
        "sentence_index": 0,
        "char_start": 0,
        "char_end": 0
      }},
      "error_type": "spelling | spacing | particle | nonstandard",
      "original": "문제가 되는 표현",
      "description": "형식적 오류 설명"
    }}
  ],
  "note": "ok | minor | many"
}}

문장 배열:
{split_text}
"""

        response = chat(prompt, system=system)
        result = self._safe_json_load(response)

        if "issues" not in result or not isinstance(result["issues"], list):
            result["issues"] = []
            result["note"] = "ok"

        return result
