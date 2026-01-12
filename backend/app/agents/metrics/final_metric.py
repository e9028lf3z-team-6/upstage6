from typing import Dict, List
from backend.app.agents.base import BaseAgent
from backend.app.llm.chat import chat


class FinalMetricAgent(BaseAgent):
    """
    최종 실행 품질 평가 메트릭 에이전트

    역할:
    - Aggregator 결과 + issue 분포를 기반으로
      '이번 실행이 어떤 상태였는지'를 사후 평가
    - 실험 비교, threshold 튜닝, 로그 분석 목적

    """

    name = "final-metrics"

    def run(
        self,
        aggregate: dict,
        tone_issues: List[dict],
        logic_issues: List[dict],
        trauma_issues: List[dict],
        hate_issues: List[dict],
        cliche_issues: List[dict],
        persona_feedback: dict | None = None,
    ) -> Dict:

        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        prompt = f"""
다음은 하나의 에이전트 파이프라인 실행 결과 요약이다.

너의 역할은 '실행 품질 평가 메트릭 에이전트'이다.

중요:
- 너는 의사결정을 하지 않는다.
- rewrite 여부 판단 금지
- 좋다/나쁘다 단정 금지
- 상대적 상태와 신호만 요약

평가 목적:
- 실험 간 비교
- threshold 조정 근거
- 운영 로그 분석

입력 요약:
- decision: {aggregate.get("decision")}
- primary_issue: {aggregate.get("primary_issue")}
- problem_types: {aggregate.get("problem_types")}
- rationale: {aggregate.get("rationale")}
- reader_confusion_detected: {aggregate.get("reader_confusion_detected")}
- reader_context_gap: {aggregate.get("reader_context_gap")}

Issue counts:
- hate: {len(hate_issues)}
- trauma: {len(trauma_issues)}
- logic: {len(logic_issues)}
- tone: {len(tone_issues)}
- cliche: {len(cliche_issues)}

Persona feedback:
{persona_feedback}

출력 JSON 형식:
{{
  "run_quality": "stable | mixed | unstable",
  "dominant_risk": "hate | trauma | logic | tone | none",
  "issue_density": "low | medium | high",
  "persona_alignment": "aligned | partial | misaligned",
  "rewrite_pressure": "low | medium | high",
  "notes": [
    "실험 또는 운영 관점에서 주목할 만한 신호 요약"
  ]
}}

판단 가이드 (강제 규칙 아님, 참고용):
- issue 다수 + persona 혼란 → unstable 가능
- trauma/hate 우세 → dominant_risk 반영
- issue 밀집도는 개수 기준 상대 판단
- rewrite_pressure는 '고쳐야 할 이유의 강도'이지 결정이 아님
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
