from typing import Dict, List
from app.agents.base import BaseAgent
from app.llm.chat import chat


class FinalMetricAgent(BaseAgent):
    """
    최종 실행 품질 평가 메트릭 에이전트

    역할:
    - 각 에이전트 결과를 기반으로 '출력 품질'을 사후 평가
    - 실험 비교, threshold 튜닝, 운영 로그 분석 목적
    - 실행 안정성 자체가 아니라 에이전트 성능 신호를 요약

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

너의 역할은 '에이전트 출력 품질 평가 메트릭'이다.

중요:
- 너는 의사결정을 하지 않는다.
- rewrite 여부 판단 금지
- 좋다/나쁘다 단정 금지
- 에이전트별 출력의 품질/안정성 신호만 요약

평가 목적:
- 에이전트별 성능 비교
- 프롬프트/규칙 튜닝 근거
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
  "overall_quality": "stable | mixed | unstable",
  "agent_performance": {{
    "tone": {{
      "quality": "good | mixed | poor",
      "signals": ["요약 신호"]
    }},
    "logic": {{
      "quality": "good | mixed | poor",
      "signals": ["요약 신호"]
    }},
    "trauma": {{
      "quality": "good | mixed | poor",
      "signals": ["요약 신호"]
    }},
    "hate_bias": {{
      "quality": "good | mixed | poor",
      "signals": ["요약 신호"]
    }},
    "genre_cliche": {{
      "quality": "good | mixed | poor",
      "signals": ["요약 신호"]
    }}
  }},
  "dominant_risk": "hate | trauma | logic | tone | none",
  "issue_density": "low | medium | high",
  "persona_alignment": "aligned | partial | misaligned",
  "notes": [
    "실험 또는 운영 관점에서 주목할 만한 신호 요약"
  ]
}}

판단 가이드 (강제 규칙 아님, 참고용):
- issue 다수 + persona 혼란 → overall_quality 하락 가능
- 특정 축만 과밀하면 해당 agent quality를 mixed/poor로 표시
- issue 밀집도는 개수 기준 상대 판단
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
