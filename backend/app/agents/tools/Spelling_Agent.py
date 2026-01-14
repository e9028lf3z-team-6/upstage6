from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import extract_split_payload
import json


class SpellingAgent(BaseAgent):
    """
    맞춤법/표기 오류 탐지 에이전트
    """

    name = "spelling-agent"

    def run(self, split_payload: object) -> dict:
        _, sentences = extract_split_payload(split_payload)
        
        all_issues = []
        chunk_size = 50  # 한 번에 분석할 문장 수
        
        for i in range(0, len(sentences), chunk_size):
            chunk = sentences[i:i + chunk_size]
            chunk_result = self._analyze_chunk(chunk, i)
            all_issues.extend(chunk_result.get("issues", []))
            
        return {
            "issues": all_issues,
            "note": f"Analyzed {len(sentences)} sentences in { (len(sentences)-1)//chunk_size + 1 } chunks"
        }

    def _analyze_chunk(self, chunk: list[str], start_index: int) -> dict:
        system = """
너는 맞춤법 오류 탐지 전용 시스템이다. 반드시 JSON만 출력한다.
"""
        split_context = json.dumps(chunk, ensure_ascii=False)
        prompt = f"""
입력은 문장 배열(JSON)이다. 시작 인덱스는 {start_index}이다.
각 문장의 sentence_index는 배열의 인덱스에 {start_index}를 더한 값이어야 한다.

역할:
- 맞춤법, 띄어쓰기, 조사, 비표준 표현만 탐지
- 수정된 문장 제시 금지

출력 형식(JSON):
{{
  "issues": [
    {{
      "issue_type": "spelling | spacing | particle | nonstandard",
      "severity": "low | medium | high",
      "sentence_index": {start_index} + index,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제가 되는 표현",
      "reason": "형식적 오류 설명",
      "confidence": 0.0
    }}
  ]
}}

문장 배열:
{split_context}
"""
        response = chat(prompt, system=system)
        return self._safe_json_load(response)
