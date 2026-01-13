from typing import Dict
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload


class TensionCurveAgent(BaseAgent):
    """
    긴장도 곡선 분석 에이전트

    역할:
    - 사건 흐름을 따라 긴장도의 변화 양상만 구조적으로 분석
    - 각 구간에서 긴장이 상승/유지/하강하는지 식별
    - 서사 구조 관점의 문제만 드러냄

    금지 사항:
    - 점수화 금지
    - 수정/재작성 제안 금지
    - 말투/안전/인과 판단 금지
    """

    name = "tension-curve-tools"

    def run(self, split_payload: object) -> Dict:
        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        split_context = format_split_payload(split_payload)

        prompt = f"""
다음은 원고를 구조적으로 분리한 결과와 문장 목록이다.

너의 역할은 '서사 긴장도 분석가'이다.
사건 흐름을 따라 독자가 느끼는 긴장도의 변화를 분석하라.

분석 기준:
- 긴장도는 독자의 심리적 몰입 관점에서 판단
- 다음 세 가지 상태 중 하나로만 분류
  * increase
  * maintain
  * decrease

지시사항:
- 점수, 수치, 그래프 좌표 생성 금지
- 수정 제안 금지
- 오직 '긴장도 흐름'과 '구조적 이상 징후'만 기술

출력 JSON 형식:
{{
  "curve": [
    {{
      "stage": "사건 흐름 단계 또는 섹션",
      "tension": "increase | maintain | decrease",
      "reason": "독자 관점에서 그렇게 판단한 간단한 이유"
    }}
  ],
  "issues": [
    {{
      "issue_type": "tension_drop | climax_missing | tension_overload | stagnation",
      "severity": "low | medium | high",
      "sentence_index": 0,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "서사 구조 관점에서의 문제 설명",
      "confidence": 0.0
    }}
  ],
  "anomalies": [
    {{
      "location": "문제 구간",
      "issue": "긴장 급락 | 클라이맥스 부재 | 긴장 과도 | 반복 정체",
      "description": "서사 구조 관점에서의 문제 설명"
    }}
  ]
}}

특별한 이상이 없다면 issues/anomalies는 빈 배열로 반환하라.

규칙:
- sentence_index는 문장 목록 JSON 배열의 인덱스다.
- char_start/end는 해당 문장 내 0-based 위치다.
- quote는 반드시 해당 문장에 존재하는 원문 그대로 사용한다.

구조 텍스트:
{split_context}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
