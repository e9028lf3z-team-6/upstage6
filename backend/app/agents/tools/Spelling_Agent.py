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

    def run(self, split_payload: object, reader_context: dict | None = None) -> dict:
        _, sentences = extract_split_payload(split_payload)
        
        all_issues = []
        chunk_size = 50  # 한 번에 분석할 문장 수
        
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunks.append((sentences[i:i + chunk_size], i))
            
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self._analyze_chunk, chunk, idx, reader_context)
                for chunk, idx in chunks
            ]
            
            for future in as_completed(futures):
                try:
                    res = future.result()
                    if res and "issues" in res:
                        all_issues.extend(res["issues"])
                except Exception as e:
                    # 개별 청크 실패 시 로그만 남기고 전체 중단 방지
                    print(f"[SpellingAgent] Chunk failed: {e}")

        # 정렬: 문장 인덱스 순
        all_issues.sort(key=lambda x: x.get("sentence_index", -1))
            
        return {
            "issues": all_issues,
            "note": f"Analyzed {len(sentences)} sentences in {len(chunks)} chunks (Parallel)"
        }

    def _analyze_chunk(self, chunk: list[str], start_index: int, reader_context: dict | None = None) -> dict:
        system = """
너는 창작물 교정 보조 시스템이다. 문학적 허용과 구어체를 존중하며, 명백한 오류만 찾아내야 한다.
반드시 JSON만 출력한다.
"""
        split_context = json.dumps(chunk, ensure_ascii=False)
        
        persona_text = ""
        if reader_context:
            persona_text = f"\n[독자 특이사항]\n{json.dumps(reader_context, ensure_ascii=False)}\n위 독자의 성향을 참고하되, 맞춤법은 표준 규범을 우선으로 판단하라."

        prompt = f"""
입력은 원고의 문장 배열(JSON)이다. 시작 인덱스는 {start_index}이다.
각 문장의 sentence_index는 {start_index} + (배열 인덱스)이다.
{persona_text}

[분석 지침]
1. **탐지 대상**:
   - 명백한 오타 (예: '갔다' -> '갓다')
   - 문맥상 명확히 틀린 조사 (예: '밥을 먹다' -> '밥이 먹다')
   - 심각한 띄어쓰기 오류 (의미 전달을 해칠 정도)

2. **무시할 대상 (Detection Exclusion)**:
   - 대화문(" ") 내부의 구어체, 비속어, 사투리
   - 의도적인 문법 파괴나 시적 허용
   - 인터넷 용어, 신조어, 의성어/의태어
   - 문장의 종결이 명사형으로 끝나는 경우 (개조식 문체)

3. **목표**:
   - 과도한 지적을 지양하고, 작가가 실수한 것으로 보이는 부분만 집어낼 것.
   - 애매하면 지적하지 말 것.

출력 형식(JSON):
{{
  "issues": [
    {{
      "issue_type": "spelling | spacing | particle",
      "severity": "low | medium | high",
      "sentence_index": {start_index} + index,
      "char_start": 0,
      "char_end": 0,
      "quote": "오류가 있는 단어 또는 어절",
      "reason": "오류라고 판단한 명확한 이유",
      "suggestion": "수정 제안 (선택)",
      "confidence": 0.8  // 0.0 ~ 1.0 (0.8 이상인 것만 출력 권장)
    }}
  ]
}}

문장 배열:
{split_context}
"""
        response = chat(prompt, system=system)
        return self._safe_json_load(response)
