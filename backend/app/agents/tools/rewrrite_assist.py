from app.agents.base import BaseAgent
from app.llm.chat import chat


class RewriteAssistAgent(BaseAgent):
    """
    수정 가이드 생성 에이전트

    원칙:
    - 실제 수정 문장 생성 X
    - 평가 / 점수화 / 등급화 X
    - Aggregator 판단 구조를 그대로 반영
    """

    name = "rewrite-assist"

    def run(
        self,
        original_text: str,
        split_text: str,
        decision_context: dict,
        tone_issues: list,
        logic_issues: list,
        trauma_issues: list | None = None,
        hate_issues: list | None = None,
        cliche_issues: list | None = None,
    ) -> dict:

        trauma_issues = trauma_issues or []
        hate_issues = hate_issues or []
        cliche_issues = cliche_issues or []

        primary_issue = decision_context.get("primary_issue")
        rationale = decision_context.get("rationale", {})
        reader_confusion = decision_context.get(
            "reader_confusion_detected", False
        )
        reader_context_gap = decision_context.get(
            "reader_context_gap", False
        )

        # Aggregator 우선순위와 반드시 동일
        priority_order = ["hate", "trauma", "logic", "tone", "genre_cliche"]

        ordered_issues = {
            "hate": hate_issues,
            "trauma": trauma_issues,
            "logic": logic_issues,
            "tone": tone_issues,
            "genre_cliche": cliche_issues,
        }

        system = """
너는 JSON 출력 전용 엔진이다.
반드시 유효한 JSON만 출력하라.
JSON 외 텍스트 출력 금지.
반드시 ASCII 쌍따옴표(")만 사용하라
"""

        prompt = f"""
다음은 원고 분석 결과를 바탕으로 생성할 '수정 가이드'다.

절대 규칙:
- 수정된 문장을 직접 제시하지 말 것
- 평가, 점수, 등급, 총평 금지
- 무엇을 왜 고쳐야 하는지만 구조적으로 안내할 것

시스템 판단 요약:
- 최종 결정: {decision_context.get("decision")}
- 최우선 이슈: {primary_issue}
- 판단 근거 요약: {rationale}

이슈 우선순위 규칙:
1. hate
2. trauma
3. logic
4. tone
5. genre_cliche (품질 개선용, 최후순위)

독자 관점 상태:
- reader_confusion_detected: {reader_confusion}
- reader_context_gap: {reader_context_gap}

이슈 목록:
- hate: {hate_issues}
- trauma: {trauma_issues}
- logic: {logic_issues}
- tone: {tone_issues}
- genre_cliche: {cliche_issues}

출력 JSON 형식:
{{
  "rewrite_type": "assist",
  "priority": "hate | trauma | logic | tone | genre_cliche",
  "guidelines": [
    {{
      "category": "hate | trauma | logic | tone | genre_cliche | reader_context",
      "reason": "왜 이 부분이 문제인지 또는 개선 대상인지",
      "focus": "어떤 관점에서 보완하거나 재구성해야 하는지"
    }}
  ],
  "note": "수정 시 유의해야 할 전체 방향성 요약"
}}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
