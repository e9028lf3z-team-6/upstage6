from app.agents.base import BaseAgent
from app.llm.chat import chat

class ReaderPersonaAgent(BaseAgent):
    """
    독자 페르소나 생성 에이전트
    - 평가/수정/판단 x
    - 독자 관점 맥락 생성 o
    """

    name = "reader-persona"

    def run(self, context: dict) -> dict:
        system = """
너는 JSON 출력 전용 엔진이다.
반드시 유효한 JSON만 출력하라.
JSON 외 텍스트 출력 금지.
"""

        prompt = f"""
다음은 글(원고/기획서)의 기본 정보다.
이 정보를 바탕으로 '회사 동료' 가상 독자 페르소나 1명을 생성하라.

규칙:
- 실존 인물 이름 금지 (가명 사용)
- 평가/수정 제안 금지
- 독자가 어떤 배경지식과 제약을 갖는지만 명확히 기술

입력 정보:
{context}

출력 JSON 형식:
{{
  "persona": {{
    "name": "가명",
    "role": "회사 동료",
    "domain": "업무 도메인",
    "seniority": "주니어|미들|시니어",
    "knowledge_level": "초급|중급|고급",
    "goals": [string],
    "constraints": [string],
    "tone_preference": string,
    "reading_style": string
  }}
}}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
