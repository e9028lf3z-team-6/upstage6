from app.agents.base import BaseAgent
from app.llm.chat import chat


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

    def run(self, split_text: str, reader_context: dict | None = None) -> dict:
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

        prompt = f"""
다음은 원고를 구조적으로 분리한 결과이다.

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
      "type": "missing_motivation | causality_gap | forced_resolution | illogical_transition",
      "from_event": "사건 A(요약)",
      "to_event": "사건 B(요약)",
      "location": "사건 흐름 단계 또는 항목",
      "description": "독자 기준에서 왜 인과가 끊기는지 간단히 설명"
    }}
  ]
}}

문제가 없다면 issues는 빈 배열로 반환하라.

구조 텍스트:
{split_text}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
