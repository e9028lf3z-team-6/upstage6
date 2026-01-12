from typing import Dict, List
from app.agents.base import BaseAgent
from app.llm.chat import chat


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

    def run(self, split_text: str) -> Dict:
        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        prompt = f"""
다음은 글을 구조적으로 분리한 텍스트이다.

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
      "location": "문제 표현 위치 또는 문단",
      "trigger_type": "사고 | 위험행동 | 재난 | 생명위협 | 공포묘사",
      "description": "독자에게 트라우마를 유발할 수 있다고 판단한 이유"
    }}
  ],
  "note": "trauma risk scan completed"
}}

특별한 위험 표현이 없으면 issues는 빈 배열로 반환하라.

분석 대상 텍스트:
{split_text}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
