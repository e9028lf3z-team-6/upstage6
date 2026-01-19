from typing import Dict, List
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload
from concurrent.futures import ThreadPoolExecutor, as_completed


class TraumaAgent(BaseAgent):
    """
    트라우마 유발 표현 탐지 에이전트
    """

    name = "trauma-tools"

    def run(self, split_payload: object) -> Dict:
        from app.agents.utils import extract_split_payload
        _, sentences = extract_split_payload(split_payload)
        
        all_issues = []
        scores = []
        chunk_size = 50
        
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunks.append((sentences[i:i + chunk_size], i))
            
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self._analyze_chunk, chunk, idx)
                for chunk, idx in chunks
            ]
            
            for future in as_completed(futures):
                try:
                    res = future.result()
                    if res:
                        if "issues" in res:
                            all_issues.extend(res["issues"])
                        if "score" in res and isinstance(res["score"], (int, float)):
                            scores.append(res["score"])
                except Exception as e:
                    print(f"[TraumaAgent] Chunk failed: {e}")

        # 정렬: 문장 인덱스 순
        all_issues.sort(key=lambda x: x.get("sentence_index", -1))
        
        # 전체 점수 계산 (평균) - 안전할수록 높음
        final_score = 100
        if scores:
            final_score = int(sum(scores) / len(scores))
            
        return {
            "score": final_score,
            "issues": all_issues,
            "note": f"Analyzed {len(sentences)} sentences in {len(chunks)} chunks (Parallel)"
        }

    def _analyze_chunk(self, chunk: list[str], start_index: int) -> dict:
        system = """
You are a strict JSON generator. You MUST output valid JSON only.
"""
        import json
        indexed_chunk = [{"id": i, "text": sent} for i, sent in enumerate(chunk)]
        split_context = json.dumps(indexed_chunk, ensure_ascii=False)

        prompt = f"""
너는 '트라우마 위험 표현 탐지기'이다.
입력은 문장 배열(JSON)이며, 각 객체는 "id"와 "text"를 가진다.

목표:
1. 독자에게 심리적 충격, 불안, 트라우마를 유발할 가능성이 있는 표현(재난, 폭력, 위험행동 등) 식별
2. 모든 설명(reason, trigger_type)은 반드시 한국어로 작성하라.

출력 JSON 형식:
{{
  "score": <int 0-100>,
  "issues": [
    {{
      "issue_type": "trauma_trigger",
      "severity": "low | medium | high",
      "ref_id": <int: 입력 객체의 "id" 값을 그대로 복사>,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "사유 (한국어로 작성)",
      "trigger_type": "사고 | 위험행동 | 재난 | 생명위협 | 공포묘사",
      "confidence": 0.0
    }}
  ]
}}

문장 배열:
{split_context}
"""
        response = chat(prompt, system=system)
        result = self._safe_json_load(response)

        # Post-processing
        if "issues" in result and isinstance(result["issues"], list):
            for issue in result["issues"]:
                ref_id = issue.pop("ref_id", None)
                if ref_id is not None and isinstance(ref_id, int):
                    issue["sentence_index"] = start_index + ref_id
                elif "sentence_index" in issue and isinstance(issue["sentence_index"], int):
                    issue["sentence_index"] = start_index + issue["sentence_index"]
        
        return result
