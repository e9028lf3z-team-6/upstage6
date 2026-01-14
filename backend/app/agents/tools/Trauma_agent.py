from typing import Dict, List
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload


class TraumaAgent(BaseAgent):
    """
    트라우마 유발 표현 탐지 에이전트

    역할:
    - 독자에게 심리적 충격, 불안, 트라우마를 유발할 수 있는 표현 탐지
    - 사고, 재난, 폭력, 위험 행동, 극단적 상황 묘사 중심
    - '위험 가능성'만 식별 (판단/차단/수정 X)

    금지 사항:
    - 수정 제안 금지
    - 수위 점수화 금지
    - 검열/차단 금지
    """

    name = "trauma-tools"

    def run(self, split_payload: object) -> Dict:
        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        split_context = format_split_payload(split_payload)

        prompt = f"""
다음은 글의 문장 목록이다.

너의 역할은 '트라우마 위험 표현 탐지기'이다.

목표:
- 독자에게 심리적 충격, 불안, 트라우마를 유발할 가능성이 있는 표현만 식별하라.

탐지 대상 예시:
- 사고, 추락, 익사, 화재, 폭발 등 재난/사고
- 위험 행동을 상세히 묘사하는 표현
- 공포, 극도의 불안, 생명 위협 상황의 직접적 서술
- 독자가 사건을 생생히 상상하게 만드는 감각적 묘사

주의 사항:
- 문학적 평가 금지
- 혐오/차별 판단 금지
- 법적 판단 금지
- 수정 제안 금지
- 위험 "가능성"만 기술

출력 JSON 형식:
{{
  "issues": [
    {{
      "issue_type": "trauma_trigger",
      "severity": "low | medium | high",
      "sentence_index": 0,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "독자에게 트라우마를 유발할 수 있다고 판단한 이유",
      "trigger_type": "사고 | 위험행동 | 재난 | 생명위협 | 공포묘사",
      "confidence": 0.0
    }}
  ],
  "note": "trauma risk scan completed"
}}

특별한 위험 표현이 없으면 issues는 빈 배열로 반환하라.

규칙:
- sentence_index는 문장 목록 JSON 배열의 인덱스다.
- char_start/end는 해당 문장 내 0-based 위치다.
- quote는 반드시 해당 문장에 존재하는 원문 그대로 사용한다.

문장 목록:
{split_context}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
