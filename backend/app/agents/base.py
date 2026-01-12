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
        - JSON이 없거나 파싱 실패 시 안전하게 빈 결과 반환
        """
        match = re.search(r"\{.*\}", text, re.DOTALL)
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
