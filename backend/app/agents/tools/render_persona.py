from app.agents.base import BaseAgent
from app.llm.chat import chat
import json

class ReaderPersonaAgent(BaseAgent):
    """
    독자 페르소나 생성 에이전트
    - 평가/수정/판단 x
    - 독자 관점 맥락 생성 o
    - 사용자가 입력한 타겟 독자층과 장르를 기반으로 구체적인 페르소나를 생성함.
    """

    name = "reader-persona"

    def run(self, context: dict) -> dict:
        system = """
너는 JSON 출력 전용 엔진이다.
반드시 유효한 JSON만 출력하라.
JSON 외 텍스트 출력 금지.
"""
        # Parse settings from context
        # context structure might vary, so we handle it safely
        settings = {}
        if isinstance(context, dict):
             # If context itself is meta_json loaded dict
            settings = context.get("settings", {})
        
        target_audience = settings.get("target_audience", "일반 대중")
        genre = settings.get("genre", "일반 글")

        # Fallback if empty strings provided
        if not target_audience: target_audience = "일반 대중"
        if not genre: genre = "일반 글"

        prompt = f"""
다음은 글(원고/기획서)의 타겟 정보이다.
이 정보를 바탕으로 해당 글을 읽을 가상의 '대표 독자(Persona)' 1명을 구체적으로 생성하라.

[입력 정보]
- 타겟 독자층: {target_audience}
- 글의 장르: {genre}

[규칙]
- 실존 인물 이름 금지 (가명 사용)
- 평가/수정 제안 금지
- 해당 독자층의 평균적인 지식 수준, 관심사, 그리고 이 글을 읽을 때 가질 법한 기대를 구체적으로 기술할 것.

출력 JSON 형식:
{{
  "persona": {{
    "name": "가명 (예: 문학소녀 김영희)",
    "role": "직업이나 사회적 역할 (예: 고등학교 국어 교사)",
    "age_group": "연령대",
    "interest_keywords": ["관심사1", "관심사2"],
    "knowledge_level": "해당 장르에 대한 지식 수준 (초급|중급|고급)",
    "expectations": ["이 글에서 기대하는 점"],
    "pain_points": ["이 글을 읽을 때 거슬릴 수 있는 요소"],
    "reading_style": "독서 성향 (예: 꼼꼼하게 분석하며 읽음, 감성에 집중함)"
  }}
}}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
