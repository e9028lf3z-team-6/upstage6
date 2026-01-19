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
        
        # Word Indexing Preprocessing
        prepared_chunk = []
        for i, sent in enumerate(chunk):
            words = sent.split()
            annotated_sent = " ".join([f"({w_idx}){word}" for w_idx, word in enumerate(words)])
            prepared_chunk.append({
                "id": i, 
                "text": annotated_sent
            })

        split_context = json.dumps(prepared_chunk, ensure_ascii=False)

        prompt = f"""
너는 '트라우마 위험 표현 탐지기'이다.
입력은 문장 배열(JSON)이다.
각 문장의 "text"는 어절마다 `(번호)단어` 형태로 인덱싱되어 있다.

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
      "ref_id": <int: 입력 객체의 "id" (문장 번호)>,
      "start_word_id": <int: 문제 구간 시작 어절 번호>,
      "end_word_id": <int: 문제 구간 끝 어절 번호>,
      "quote": "문제 구간 단어들",
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

        # Post-processing: Word ID -> Char Offset
        if "issues" in result and isinstance(result["issues"], list):
            for issue in result["issues"]:
                ref_id = issue.pop("ref_id", None)
                if ref_id is not None and isinstance(ref_id, int):
                    issue["sentence_index"] = start_index + ref_id
                    
                    s_id = issue.get("start_word_id")
                    e_id = issue.get("end_word_id")
                    
                    if s_id is None and "word_id" in issue:
                        s_id = issue["word_id"]
                        e_id = s_id

                    if isinstance(s_id, int) and isinstance(e_id, int) and 0 <= ref_id < len(chunk):
                        origin_sent = chunk[ref_id]
                        words = origin_sent.split()
                        
                        if 0 <= s_id < len(words) and 0 <= e_id < len(words) and s_id <= e_id:
                            start_pos = -1
                            end_pos = -1
                            current_pos = 0
                            
                            for w_idx, w in enumerate(words):
                                found_idx = origin_sent.find(w, current_pos)
                                if found_idx != -1:
                                    if w_idx == s_id:
                                        start_pos = found_idx
                                    if w_idx == e_id:
                                        end_pos = found_idx + len(w)
                                        break
                                    current_pos = found_idx + len(w)
                            
                            if start_pos != -1 and end_pos != -1:
                                issue["char_start"] = start_pos
                                issue["char_end"] = end_pos
                                issue["quote"] = origin_sent[start_pos:end_pos]

                elif "sentence_index" in issue and isinstance(issue["sentence_index"], int):
                    issue["sentence_index"] = start_index + issue["sentence_index"]
        
        return result
