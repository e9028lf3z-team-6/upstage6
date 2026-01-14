from typing import Dict
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload


class HateBiasAgent(BaseAgent):
    """
    혐오/편견 표현 탐지 에이전트
    """

    name = "hate-bias-tools"

    def run(self, split_payload: object) -> Dict:
        from app.agents.utils import extract_split_payload
        _, sentences = extract_split_payload(split_payload)
        
        all_issues = []
        chunk_size = 50
        
        for i in range(0, len(sentences), chunk_size):
            chunk = sentences[i:i + chunk_size]
            chunk_result = self._analyze_chunk(chunk, i)
            all_issues.extend(chunk_result.get("issues", []))
            
        return {
            "issues": all_issues,
            "note": f"Analyzed in chunks. Total issues: {len(all_issues)}"
        }

    def _analyze_chunk(self, chunk: list[str], start_index: int) -> dict:
        system = """
You are a strict JSON generator. You MUST output valid JSON only.
"""
        import json
        split_context = json.dumps(chunk, ensure_ascii=False)

        prompt = f"""
너는 '혐오 및 편견 표현 탐지기'이다.
입력은 원고의 문장 배열(JSON)이며, 시작 인덱스는 {start_index}이다.
각 이슈의 sentence_index는 {start_index} + (청크 내 인덱스)로 계산해야 한다.

핵심 원칙:
- 반드시 '집단적 속성'과 연결된 경우만 issue로 판단할 것
- 탐지 대상: 특정 집단 일반화, 성별/민족/직업 등 고정관념, 비하

출력 JSON 형식:
{{
  "issues": [
    {{
      "issue_type": "bias | hate | stereotype",
      "severity": "low | medium | high",
      "sentence_index": {start_index} + index,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "사유",
      "target": "집단/대상",
      "bias_type": "혐오 | 편견 | 비하 | 고정관념",
      "confidence": 0.0
    }}
  ]
}}

문장 배열:
{split_context}
"""
        response = chat(prompt, system=system)
        return self._safe_json_load(response)
