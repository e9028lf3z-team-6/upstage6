from app.agents.base import BaseAgent
from app.llm.chat import chat


class RewriteAssistAgent(BaseAgent):
    """
    수정 가이드 생성 에이전트

    원칙:
    - 실제 수정 문장 생성 X
    - 평가 / 점수화 / 등급화 X
    - Aggregator 판단 구조를 그대로 반영
    - spelling은 surface-level 가이드로만 제공
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
        spelling_issues: list | None = None,   # ✅ 추가
    ) -> dict:

        trauma_issues = trauma_issues or []
        hate_issues = hate_issues or []
        cliche_issues = cliche_issues or []
        spelling_issues = spelling_issues or []

        # --- 토큰 최적화 로직 시작 ---
        def _optimize_issues(issues: list, limit: int = 20) -> list:
            """
            토큰 제한을 방지하기 위해 이슈 리스트를 축소합니다.
            - 상위 N개만 유지
            - 인용문(quote) 길이 제한
            """
            if not issues:
                return []
            
            optimized = []
            for item in issues[:limit]:
                # 얕은 복사로 원본 보존
                new_item = item.copy()
                # 긴 텍스트 필드 축소
                for key in ['quote', 'original', 'description', 'reason']:
                    if key in new_item and isinstance(new_item[key], str) and len(new_item[key]) > 100:
                        new_item[key] = new_item[key][:100] + "..."
                optimized.append(new_item)
            return optimized

        # 각 카테고리별 이슈 최적화 (가이드 생성용 요약)
        opt_hate = _optimize_issues(hate_issues)
        opt_trauma = _optimize_issues(trauma_issues)
        opt_logic = _optimize_issues(logic_issues)
        opt_tone = _optimize_issues(tone_issues)
        opt_cliche = _optimize_issues(cliche_issues)
        opt_spelling = _optimize_issues(spelling_issues)
        # --- 토큰 최적화 로직 끝 ---

        primary_issue = decision_context.get("primary_issue")
        rationale = decision_context.get("rationale", {})
        surface_issues = decision_context.get("surface_issues", {})

        reader_confusion = decision_context.get(
            "reader_confusion_detected", False
        )
        reader_context_gap = decision_context.get(
            "reader_context_gap", False
        )

        # Aggregator 우선순위와 반드시 동일
        priority_order = ["hate", "trauma", "logic", "tone", "cliche"]

        system = """
너는 JSON 출력 전용 엔진이다.
반드시 유효한 JSON만 출력하라.
JSON 외 텍스트 출력 금지.
반드시 ASCII 쌍따옴표(")만 사용하라.
"""

        prompt = f"""
다음은 원고 분석 결과를 바탕으로 생성할 '수정 가이드'다.

절대 규칙:
- 수정된 문장을 직접 제시하지 말 것
- 평가, 점수, 등급, 총평 금지
- 무엇을 왜 고쳐야 하는지만 구조적으로 안내할 것
- spelling(맞춤법/띄어쓰기)은 의미 수정 없이 별도 정리 대상으로만 다룰 것

시스템 판단 요약:
- 최종 결정: {decision_context.get("decision")}
- 최우선 이슈: {primary_issue}
- 판단 근거 요약: {rationale}

표면적 문제 요약(surface-level):
- spelling_count: {surface_issues.get("spelling", 0)}

이슈 우선순위 규칙:
1. hate
2. trauma
3. logic
4. tone
5. cliche (품질 개선용, 최후순위)
6. spelling (의미 비개입, 표기 정리 전용)

독자 관점 상태:
- reader_confusion_detected: {reader_confusion}
- reader_context_gap: {reader_context_gap}

이슈 목록 (일부 요약됨):
- hate (총 {len(hate_issues)}건): {opt_hate}
- trauma (총 {len(trauma_issues)}건): {opt_trauma}
- logic (총 {len(logic_issues)}건): {opt_logic}
- tone (총 {len(tone_issues)}건): {opt_tone}
- cliche (총 {len(cliche_issues)}건): {opt_cliche}
- spelling (총 {len(spelling_issues)}건): {opt_spelling}

작성 지침:
- 각 guideline에는 아래 4가지 키를 반드시 포함
  1) reason: 왜 문제가 되는지
  2) focus: 어떤 관점에서 고쳐야 하는지
  3) approach: 구체적인 수정 방향(예: 완화, 명시, 재배치, 맥락 추가)
  4) outcome: 고친 후 독자가 기대할 변화(혼란 감소, 신뢰도 상승 등)
- 동일한 이유의 반복 금지
- 이슈별로 1~2개 가이드만 작성

출력 JSON 형식:
{{
  "rewrite_type": "assist",
  "priority": "hate | trauma | logic | tone | cliche | spelling",
  "guidelines": [
    {{
      "category": "hate | trauma | logic | tone | cliche | reader_context | spelling",
      "reason": "왜 이 부분이 문제이거나 정리가 필요한지",
      "focus": "어떤 관점에서 보완하거나 정리해야 하는지",
      "approach": "구체적인 수정 방향",
      "outcome": "수정 후 기대되는 독자 반응"
    }}
  ],
  "note": "수정 시 유의해야 할 전체 방향성 요약"
}}
"""

        response = chat(prompt, system=system)
        result = self._safe_json_load(response)

        # 방어 로직
        if "guidelines" not in result:
            result["guidelines"] = []

        return result
