from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload


class CausalityEvaluatorAgent(BaseAgent):
    """
    인과관계 연결 분석 에이전트 (Causality Expert)

    역할:
    - 사건 A -> 사건 B 전환에서 인과가 끊기는 지점만 식별
    - 점수/등급/총평 금지
    - 수정 문장/재작성 금지
    - 말투/표현/안전 판단 금지 (인과관계만)

    독자 수준(knowledge_level)에 따라 '설명 부족' 판단 민감도만 조절한다.
    """

    name = "causality_agent"

    def run(self, split_payload: object, reader_context: dict | None = None) -> dict:
        """
        reader_context 예시:
        {
          "knowledge_level": "초급|중급|고급"
        }
        """

        knowledge_level = "중급"
        if reader_context:
            knowledge_level = reader_context.get("knowledge_level", "중급")

        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        split_context = format_split_payload(split_payload)

        prompt = f"""
다음은 원고를 구조적으로 분리한 결과와 문장 목록이다.

너의 역할은 '인과관계 분석가'이다.
오직 사건 간 인과 연결만 보고, 인과가 끊기는 지점을 식별하라.

독자 이해 수준:
- 초급: 인과 관계, 동기, 전제가 명시되지 않으면 문제로 간주
- 중급: 핵심 인과와 동기가 누락된 경우만 문제로 간주
- 고급: 암시적 연결은 허용하되 명백한 인과 단절만 문제로 간주

현재 독자 수준: {knowledge_level}

지시사항:
- 점수, 등급, 총평 금지
- 수정 제안 금지
- 말투/표현/안전성 판단 금지
- 오직 인과관계 이해가 끊기는 지점만 식별

출력 형식(JSON):
{{
  "issues": [
    {{
      "issue_type": "missing_motivation | causality_gap | forced_resolution | illogical_transition",
      "severity": "low | medium | high",
      "sentence_index": 0,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "독자 기준에서 왜 인과가 끊기는지 간단히 설명",
      "from_event": "사건 A(요약)",
      "to_event": "사건 B(요약)",
      "confidence": 0.0
    }}
  ]
}}

문제가 없다면 issues는 빈 배열로 반환하라.

규칙:
- sentence_index는 문장 목록 JSON 배열의 인덱스다.
- char_start/end는 해당 문장 내 0-based 위치다.
- quote는 반드시 해당 문장에 존재하는 원문 그대로 사용한다.

구조 텍스트:
{split_context}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
