from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload
import json

class PersonaFeedbackAgent(BaseAgent):
    """
    독자 페르소나 관점 피드백 에이전트

    출력 목적:
    - Aggregator가 '독자 혼란 신호'를 감지하기 위한 근거 제공
    """

    name = "persona-feedback"

    def run(self, persona: dict, split_payload: object) -> dict:
        system = """
너는 JSON 출력 전용 엔진이다.
반드시 유효한 JSON만 출력하라.
JSON 외 텍스트 출력 금지.
"""

        split_context = format_split_payload(split_payload)
        
        # Extract persona details safely
        p_data = persona.get("persona", {})
        p_info = json.dumps(p_data, ensure_ascii=False, indent=2)

        prompt = f"""
다음은 독자 페르소나와 원고 문장 목록이다.
제시된 페르소나에 완전히 이입하여, 해당 독자의 시각과 지식 수준에서 글을 읽고 피드백을 생성하라.

[독자 프로필]
{p_info}

[문장 목록]
{split_context}

[규칙]
- 점수/등급/총평 금지
- 수정 문장 제안 금지
- **기술적 구현(OCR, API, 데이터 처리, 코딩 등)에 대한 언급 절대 금지** (단, 원고 내용이 기술 문서라면 예외)
- 오직 '독자가 읽다가 이해가 안 되거나, 몰입이 깨지는 지점'만 기록

[작성 지침]
1. **confusions**: 문맥상 이해가 안 되거나, 독자의 배경지식으로 해석하기 어려운 부분.
2. **missing_context**: 앞뒤 설명이 부족하여 상상하기 어려운 부분.
3. **questions_to_author**: 독자가 작가에게 물어보고 싶은 순수한 호기심이나 의문.

출력 JSON 형식:
{{
  "persona_feedback": {{
    "persona_name": "{p_data.get('name', '독자')}",
    "confusions": ["문장 인덱스 또는 내용: 이유"],
    "missing_context": ["내용: 이유"],
    "questions_to_author": ["질문 내용"]
  }}
}}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
