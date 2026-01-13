from typing import Dict
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload


class HateBiasAgent(BaseAgent):
    """
    혐오/편견 표현 탐지 에이전트

    역할:
    - 집단적 속성(국가, 성별, 직업, 신체, 질병, 민족 등)에 대한
      혐오·편견·차별 가능성이 있는 표현만 탐지
    - 은유적/암시적 고정관념은 포함하되,
      '개인 단독 사례'는 원칙적으로 제외

    금지 사항:
    - 법적 판단 금지
    - 검열/차단 금지
    - 수정 제안 금지
    - 트라우마/안전 판단 금지
    """

    name = "hate-bias-tools"

    def run(self, split_payload: object) -> Dict:
        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        split_context = format_split_payload(split_payload)

        prompt = f"""
다음은 글을 구조적으로 분리한 텍스트와 문장 목록이다.

너의 역할은 '혐오 및 편견 표현 탐지기'이다.

핵심 원칙 (중요):
- 반드시 '집단적 속성'과 연결된 경우만 issue로 판단할 것
- 단일 개인의 이름, 행동, 사건은 원칙적으로 혐오/편견으로 판단하지 말 것
- 실제 인물 이름과의 '단순한 동일성'만으로는 편견으로 판단하지 말 것

탐지 대상 (O):
- 특정 집단을 일반화하거나 열등/위험/부정적으로 묘사
- 성별, 민족, 국가, 직업, 신체·정신적 특성에 대한 고정관념
- 집단 전체에 속성을 전이시키는 비교·비유

비탐지 대상 (X):
- 가상의 등장인물 이름
- 개인의 단발적 행동
- 사건 묘사 자체
- 위험 행동 (→ trauma 영역)
- 공포/사고/재난 묘사 (→ trauma 영역)

주의 사항:
- 풍자/비판 여부 판단 금지
- 의도 추정 금지
- 법적 결론 금지
- 수정 제안 금지
- 오직 '편견으로 해석될 가능성'만 기술

출력 JSON 형식:
{{
  "issues": [
    {{
      "issue_type": "bias | hate | stereotype",
      "severity": "low | medium | high",
      "sentence_index": 0,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "집단 일반화 또는 차별로 해석될 수 있는 이유",
      "target": "집단/대상 (예: 특정 집단, 성별, 국가, 직업 등)",
      "bias_type": "혐오 | 편견 | 비하 | 고정관념",
      "confidence": 0.0
    }}
  ],
  "note": "hate and bias scan completed"
}}

특별한 문제가 없으면 issues는 빈 배열로 반환하라.

규칙:
- sentence_index는 문장 목록 JSON 배열의 인덱스다.
- char_start/end는 해당 문장 내 0-based 위치다.
- quote는 반드시 해당 문장에 존재하는 원문 그대로 사용한다.

분석 대상 텍스트:
{split_context}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
