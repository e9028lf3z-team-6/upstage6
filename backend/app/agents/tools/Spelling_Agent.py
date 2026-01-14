from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import extract_split_payload
import json


class SpellingAgent(BaseAgent):
    """
    맞춤법/표기 오류 탐지 에이전트

    역할:
    - 문장 단위로 분리된 텍스트를 입력으로 받음
    - 맞춤법, 띄어쓰기, 조사, 비표준 표현만 탐지
    - 평가, 점수, 수정 제안은 하지 않음
    """

    name = "spelling-agent"

    def run(self, split_payload: object) -> dict:
        system = """
너는 맞춤법 오류 탐지 전용 시스템이다.
반드시 JSON만 출력한다.
설명, 문장, 마크다운, 추가 텍스트 출력 금지.
"""

        _, sentences = extract_split_payload(split_payload)
        split_context = json.dumps(sentences, ensure_ascii=False)

        prompt = f"""
입력은 문장 배열(JSON)이다.
index는 0부터 시작한다.

역할:
- 맞춤법, 띄어쓰기, 조사, 비표준 표현만 탐지
- 의미, 논리, 말투 평가는 하지 말 것
- 수정된 문장 제시 금지

출력 형식(JSON):
{{
  "issues": [
    {{
      "issue_type": "spelling | spacing | particle | nonstandard",
      "severity": "low | medium | high",
      "sentence_index": 0,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제가 되는 표현",
      "reason": "형식적 오류 설명",
      "confidence": 0.0
    }}
  ],
  "note": "ok | minor | many"
}}

규칙:
- sentence_index는 문장 목록 JSON 배열의 인덱스다.
- char_start/end는 해당 문장 내 0-based 위치다.
- quote는 반드시 해당 문장에 존재하는 원문 그대로 사용한다.

문장 배열:
{split_context}
"""

        response = chat(prompt, system=system)
        result = self._safe_json_load(response)

        if "issues" not in result or not isinstance(result["issues"], list):
            result["issues"] = []
            result["note"] = "ok"

        return result
