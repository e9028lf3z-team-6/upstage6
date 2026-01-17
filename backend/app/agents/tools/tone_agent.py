from app.agents.base import BaseAgent
from app.llm.chat import chat
import json
import re
from app.agents.utils import format_split_payload


class ToneEvaluatorAgent(BaseAgent):
    """
    말투 분석 전문 에이전트

    역할:
    - 문장 목록을 입력으로 받음
    - 말투/서술 방식으로 인해 독자가 개연성을 느끼기 어려운 지점을 식별
    - 독자 경험 관점의 문제 지점만 표기

    하지 않는 것:
    - 점수 산출
    - 논리적 정합성 판정
    - 수정/대체 문장 제안
    """

    name = "tone-evaluator"

    def run(self, split_payload: object, reader_context: dict | None = None, global_summary: str | None = None) -> dict:
        system = """
        너는 JSON 출력 전용 엔진이다.
        반드시 유효한 JSON만 출력해야 한다.
        설명, 마크다운, 주석, 일반 텍스트를 절대 포함하지 마라.
        JSON 이외의 어떠한 문자열도 출력해서는 안 된다.
        """

        split_context = format_split_payload(split_payload)
        
        persona_text = ""
        if reader_context:
            persona_text = f"\n[독자 페르소나 정보]\n{json.dumps(reader_context, ensure_ascii=False)}\n위 독자의 성향과 배경지식을 고려하여, 해당 독자가 이질감을 느낄 만한 말투를 분석하라."

        prompt = f"""
        다음은 원고의 문장 목록이다.

        너의 역할은 단순한 분석가가 아니라, **철저한 '독자 대변인(Reader Advocate)'**이다.
        네 개인적인 기준이나 보편적인 기준은 중요하지 않다.
        오직 **[독자 페르소나 정보]에 정의된 특정 독자의 입장**에서만 판단하라.

        [전체 맥락 요약 (참조용)]
        {global_summary or "제공되지 않음"}
        {persona_text}

        행동 강령:
        1. **독자 빙의**: 위 독자가 이 글을 읽는다고 상상하라. 이 독자가 불편함, 어색함, 지루함을 느낄만한 지점을 찾아내라.
        2. **적극적 방어**: 보편적으로는 허용되는 말투라도, 이 독자의 성향(연령, 배경, 취향)에 맞지 않으면 가차 없이 지적하라.
        3. **이유 명시**: 지적할 때는 "이 독자는 ~한 성향이므로 이 표현을 ~하게 느낄 것이다"라고 독자 관점에서 이유를 설명하라.

        반드시 지켜야 할 규칙:
        - 점수, 등급, 총평을 만들지 말 것
        - 문장을 수정하거나 대체 표현을 제안하지 말 것
        - 오직 '독자 관점에서 개연성이 약해지는 말투 지점'만 식별할 것
        - [전체 맥락 요약]을 참고하여, 인물의 말투가 상황이나 설정에 어긋나는지 확인하라.

        분석 기준 (개연성 중심):
        - 말투 변화가 맥락 없이 발생하는 지점
        - 감정 톤이 사건 전개와 어긋나는 부분
        - 독자 입장에서 설명 없이 받아들이기 어려운 어조
        - 말투 때문에 인과관계가 암묵적으로 생략된 느낌을 주는 부분
        - 독자 수준 대비 과도하거나 부족한 서술

        출력 형식(JSON):
        {{
          "issues": [
            {{
              "issue_type": "tone_shift | tone_mismatch | register_mismatch",
              "severity": "low | medium | high",
              "sentence_index": 0,
              "char_start": 0,
              "char_end": 0,
              "quote": "문제 구간 원문 인용",
              "reason": "개연성 관점의 문제 요약",
              "confidence": 0.0
            }}
          ],
          "note": "말투 전반에서 관찰된 독자 인지 흐름 특성 요약 (선택)"
        }}

        규칙:
        - sentence_index는 문장 목록 JSON 배열의 인덱스다.
        - char_start/end는 해당 문장 내 0-based 위치다.
        - quote는 반드시 해당 문장에 존재하는 원문 그대로 사용한다.

        문장 목록:
        {split_context}
        """

        response = chat(prompt, system=system)
        return self._safe_json_load(response)

    def _safe_json_load(self, text: str) -> dict:
        """
        LLM 출력이 깨져도 서버를 죽이지 않는 안전 파서
        """

        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {
                "issues": [],
                "note": "LLM output did not contain JSON block",
                "_raw": text[:300],
            }

        json_str = match.group()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            return {
                "issues": [],
                "note": "JSON decode failed, degraded safely",
                "error": str(e),
                "_raw": json_str[:300],
            }
