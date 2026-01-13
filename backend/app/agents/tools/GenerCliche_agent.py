from typing import Dict
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload


class GenreClicheAgent(BaseAgent):
    """
    장르 클리셰 탐지 에이전트

    역할:
    - 특정 장르에서 반복적으로 사용되는 전형적 서사 패턴(클리셰)을 식별
    - 장르 기대에 비해 과도하게 익숙하거나 예측 가능한 전개를 탐지

    원칙:
    - 평가/점수화 금지
    - 수정 제안 금지
    - 창작 방향 제시 금지
    - 오류/문제 단정 금지
    - '클리셰로 해석될 수 있음' 수준의 가능성만 기술

    금지 사항:
    - 혐오/트라우마/안전 판단 금지
    - 논리적 옳고 그름 판단 금지
    """

    name = "genre-cliche-tools"

    def run(self, split_payload: object) -> Dict:
        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        split_context = format_split_payload(split_payload)

        prompt = f"""
다음은 서사를 구조적으로 분리한 텍스트와 문장 목록이다.

너의 역할은 '장르 클리셰 탐지기'이다.

목표:
- 서사 전개에서 특정 장르에서 자주 반복되는 전형적 패턴을 식별하라.
- 해당 패턴이 '익숙한 클리셰로 인식될 가능성'만 기술하라.

탐지 대상 예시:
- 성장 서사에서 위기 상황 중 갑작스러운 각성
- 조력자 없이 주인공 혼자 문제를 해결하는 전형적 전개
- 극적인 사건 직후 빠른 정서적 안정
- 일상적 배경에서 돌발적 사고 → 즉각적 영웅화

비탐지 대상:
- 장르 자체의 기본 구조 설명
- 논리적 오류 여부
- 사실적 정확성 문제
- 감정 표현의 적절성
- 혐오/트라우마 요소

주의 사항:
- 클리셰는 '나쁜 것'이 아니다.
- 창의성 부족 판단 금지
- 수정 제안 금지
- 오직 독자 인식 관점에서의 '전형성 가능성'만 기술

출력 JSON 형식:
{{
  "issues": [
    {{
      "issue_type": "cliche_pattern",
      "severity": "low | medium | high",
      "sentence_index": 0,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "왜 독자에게 익숙한 클리셰로 인식될 수 있는지 설명",
      "genre": "추정 장르 (예: 성장, 드라마, 액션 등)",
      "pattern": "전형적으로 반복되는 서사 패턴 요약",
      "confidence": 0.0
    }}
  ],
  "note": "genre cliche scan completed"
}}

특별한 클리셰가 감지되지 않으면 issues는 빈 배열로 반환하라.

규칙:
- sentence_index는 문장 목록 JSON 배열의 인덱스다.
- char_start/end는 해당 문장 내 0-based 위치다.
- quote는 반드시 해당 문장에 존재하는 원문 그대로 사용한다.

분석 대상 텍스트:
{split_context}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
