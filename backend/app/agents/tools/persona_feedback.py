from backend.app.agents.base import BaseAgent
from backend.app.llm.chat import chat


class PersonaFeedbackAgent(BaseAgent):
    """
    독자 페르소나 관점 피드백 에이전트

    출력 목적:
    - Aggregator가 '독자 혼란 신호'를 감지하기 위한 근거 제공
    """

    name = "persona-feedback"

    def run(self, persona: dict, split_text: str) -> dict:
        system = """
너는 JSON 출력 전용 엔진이다.
반드시 유효한 JSON만 출력하라.
JSON 외 텍스트 출력 금지.
"""

        prompt = f"""
다음은 독자 페르소나와 원고 분리 결과이다.
페르소나 관점에서 글을 읽었다고 가정하고 피드백을 생성하라.

규칙:
- 점수/등급/총평 금지
- 수정 문장 제안 금지
- 평가 표현(좋다/나쁘다/문제다) 금지
- 말투/논리/안전성에 대한 판정 금지
- 오직 '읽다가 이해가 멈추는 지점'만 기록

작성 지침:
- confusions: 읽는 흐름이 끊기거나 의미가 불명확한 지점
- missing_context: 이해에 필요한 배경 정보가 부족한 지점
- questions_to_author: 독자가 자연스럽게 떠올리는 확인 질문

페르소나:
{persona}

분리 결과:
{split_text}

출력 JSON 형식:
{{
  "persona_feedback": {{
    "persona_name": "{persona.get('persona', {}).get('name', '가명')}",
    "confusions": [string],
    "missing_context": [string],
    "questions_to_author": [string]
  }}
}}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
