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

        # [Word Indexing 전처리]
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
입력은 원고의 문장 배열(JSON)이다.
각 문장의 "text"는 어절마다 `(번호)단어` 형태로 인덱싱되어 있다.

[분석 지침]
1. 탐지 대상: 오타, 문맥상 틀린 조사, 심각한 띄어쓰기 오류
2. 무시 대상: 대화문, 사투리, 시적 허용, 인터넷 용어
3. 목표: 명백한 실수만 지적

출력 형식(JSON):
{{
  "score": <int 0-100>,
  "issues": [
    {{
      "issue_type": "spelling | spacing | particle",
      "severity": "low | medium | high",
      "ref_id": <int: 입력 객체의 "id" (문장 번호)>,
      "start_word_id": <int: 문제 구간의 시작 어절 번호>,
      "end_word_id": <int: 문제 구간의 끝 어절 번호 (단어 하나면 start_word_id와 동일)>,
      "quote": "문제 구간 단어들 (참고용)",
      "reason": "오류 이유",
      "suggestion": "수정 제안",
      "confidence": 0.8
    }}
  ]
}}

문장 배열:
{split_context}
"""
        response = chat(prompt, system=system)
        result = self._safe_json_load(response)
        
        # [후처리] Word IDs -> Char Offset 변환
        if "issues" in result and isinstance(result["issues"], list):
            for issue in result["issues"]:
                # 1. 문장 인덱스 복원
                ref_id = issue.pop("ref_id", None)
                if ref_id is not None and isinstance(ref_id, int):
                    issue["sentence_index"] = start_index + ref_id
                    
                    # 2. 어절 인덱스로 char_start/end 계산
                    s_id = issue.get("start_word_id")
                    e_id = issue.get("end_word_id")
                    
                    # 호환성: word_id만 있는 경우 처리
                    if s_id is None and "word_id" in issue:
                        s_id = issue["word_id"]
                        e_id = s_id

                    if isinstance(s_id, int) and isinstance(e_id, int) and 0 <= ref_id < len(chunk):
                        origin_sent = chunk[ref_id]
                        words = origin_sent.split()
                        
                        if 0 <= s_id < len(words) and 0 <= e_id < len(words) and s_id <= e_id:
                            # 시작 위치 찾기
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
                                        # 종료 지점까지 찾았으면 중단
                                        break
                                    
                                    current_pos = found_idx + len(w)
                            
                            if start_pos != -1 and end_pos != -1:
                                issue["char_start"] = start_pos
                                issue["char_end"] = end_pos
                                # quote 갱신 (정확한 원본 텍스트로)
                                issue["quote"] = origin_sent[start_pos:end_pos]

                elif "sentence_index" in issue and isinstance(issue["sentence_index"], int):
                    issue["sentence_index"] = start_index + issue["sentence_index"]
                    
        return result
