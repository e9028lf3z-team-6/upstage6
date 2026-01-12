import json
import re


class BaseAgent:
    """
    모든 에이전트의 공통 베이스 클래스

    - LLM 호출 결과(JSON)를 안전하게 파싱하기 위한
      공통 유틸리티를 제공
    """

    def _safe_json_load(self, text: str) -> dict:
        import json, re

        if not text:
            return {"issues": []}

        # 가장 바깥 JSON만 추출
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            # JSON이 없으면 "문제 없음"으로 처리
            return {"issues": []}

        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {"issues": []}

