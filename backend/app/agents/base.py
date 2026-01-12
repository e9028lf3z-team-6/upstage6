import json
import re


class BaseAgent:
    """
    모든 에이전트의 공통 베이스 클래스

    - LLM 호출 결과(JSON)를 안전하게 파싱하기 위한
      공통 유틸리티를 제공
    """

    def _safe_json_load(self, text: str) -> dict:
        """
        LLM 출력에서 JSON 블록만 추출하여 dict로 변환

        - LLM이 설명/문장/개행을 섞어 출력하는 경우에도 대응
        - JSON이 없으면 명확한 에러 발생
        """
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"LLM did not return valid JSON: {text}")

        return json.loads(match.group())
