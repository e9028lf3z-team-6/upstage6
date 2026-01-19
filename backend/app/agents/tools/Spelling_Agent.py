from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import extract_split_payload
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


class SpellingAgent(BaseAgent):
    """
    맞춤법/표기 오류 탐지 에이전트
    """

    name = "spelling-agent"

    def run(self, split_payload: object) -> dict:
        _, sentences = extract_split_payload(split_payload)
        
        all_issues = []
        scores = []
        chunk_size = 30  # 한 번에 분석할 문장 수 (속도 개선을 위해 축소)
        
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunks.append((sentences[i:i + chunk_size], i))
            
        with ThreadPoolExecutor(max_workers=8) as executor:  # 병렬 처리 수 확대
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
                    # 개별 청크 실패 시 로그만 남기고 전체 중단 방지
                    print(f"[SpellingAgent] Chunk failed: {e}")

        # 정렬: 문장 인덱스 순
        all_issues.sort(key=lambda x: x.get("sentence_index", -1))
        
        # 전체 점수 계산 (평균)
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
너는 창작물 교정 보조 시스템이다.
반드시 JSON만 출력한다.
"""
        import json
        # ID를 명시적으로 부여 (0부터 시작하는 상대값)
        indexed_chunk = [{"id": i, "text": sent} for i, sent in enumerate(chunk)]
        split_context = json.dumps(indexed_chunk, ensure_ascii=False)

        prompt = f"""
입력은 원고의 문장 배열(JSON)이다. 각 객체는 "id"와 "text"를 가진다.

[분석 지침]
1. **탐지 대상**:
   - 명백한 오타 (예: '갔다' -> '갓다')
   - 문맥상 명확히 틀린 조사 (예: '밥을 먹다' -> '밥이 먹다')
   - 심각한 띄어쓰기 오류 (의미 전달을 해칠 정도)

2. **무시할 대상**:
   - 대화문, 사투리, 시적 허용, 인터넷 용어

3. **목표**:
   - 과도한 지적 지양. 명백한 실수만 지적.

출력 형식(JSON):
{{
  "score": <int 0-100>,
  "issues": [
    {{
      "issue_type": "spelling | spacing | particle",
      "severity": "low | medium | high",
      "ref_id": <int: 입력 객체의 "id" 값을 그대로 복사>,
      "char_start": 0,
      "char_end": 0,
      "quote": "오류가 있는 단어 또는 어절",
      "reason": "오류라고 판단한 명확한 이유",
      "suggestion": "수정 제안 (선택)",
      "confidence": 0.8
    }}
  ]
}}

문장 배열:
{split_context}
"""
        response = chat(prompt, system=system)
        result = self._safe_json_load(response)
        
        # Post-processing: Map ref_id back to absolute sentence_index
        if "issues" in result and isinstance(result["issues"], list):
            for issue in result["issues"]:
                # ref_id를 확인하고 sentence_index로 변환
                ref_id = issue.pop("ref_id", None) # ref_id는 제거하고 sentence_index로 변경
                if ref_id is not None and isinstance(ref_id, int):
                    issue["sentence_index"] = start_index + ref_id
                elif "sentence_index" in issue and isinstance(issue["sentence_index"], int):
                    # 혹시 LLM이 습관적으로 sentence_index를 썼을 경우 대비 (상대 인덱스로 가정)
                    issue["sentence_index"] = start_index + issue["sentence_index"]
                    
        return result
