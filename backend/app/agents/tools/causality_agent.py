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

    def run(self, split_payload: object, global_summary: str | None = None, persona: dict | None = None) -> dict:
        
        persona_text = ""
        knowledge_level = "중급" # Default fallback
        
        if persona:
            # 페르소나 정보를 기반으로 독자 수준 추론 (단순 매핑)
            age = str(persona.get('age', ''))
            job = persona.get('job', '')
            # 예시 로직: 10대 이하면 초급, 전문직이면 고급 등 (여기선 단순 텍스트로 전달)
            
            persona_text = f"""
            [독자 페르소나]
            - 나이/직업: {age} / {job}
            - 성향: {persona.get('trait', '정보 없음')}
            - 독서 취향: {persona.get('preference', '정보 없음')}
            
            위 독자가 이 글을 읽는다고 가정하고 평가하라.
            """

        system = """
You are a strict JSON generator.
You MUST output valid JSON only.
Do NOT include explanations or markdown.
"""

        split_context = format_split_payload(split_payload)

        prompt = f"""
다음은 원고의 문장 목록이다.

너의 역할은 '인과관계 분석가'이다.
오직 사건 간 인과 연결만 보고, 인과가 끊기는 지점을 식별하라.

[전체 맥락 요약 (참조용)]
{global_summary or "제공되지 않음"}

{persona_text}

지시사항:
1. 사건 간 인과 연결이 끊기거나 비약이 심한 지점(이슈)을 식별하라.
2. 글 전체의 논리적 완결성과 개연성을 0~100점 사이의 점수('score')로 평가하라.
3. 수정 제안 금지
4. 말투/표현/안전성 판단 금지
5. [전체 맥락 요약]을 참고하여, 앞부분의 설정이 뒷부분에서 어긋나는지(개연성) 확인하라.

출력 형식(JSON):
{{
  "score": <int 0-100, 독자가 느끼는 논리적 완결성 점수>,
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

문장 목록:
{split_context}
"""

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
