from typing import Dict
from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.agents.utils import format_split_payload
from concurrent.futures import ThreadPoolExecutor, as_completed


class HateBiasAgent(BaseAgent):
    """
    혐오/편견 표현 탐지 에이전트
    """

    name = "hate-bias-tools"

    def run(self, split_payload: object, reader_context: dict | None = None) -> Dict:
        from app.agents.utils import extract_split_payload
        _, sentences = extract_split_payload(split_payload)
        
        all_issues = []
        chunk_size = 50
        
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
                    print(f"[HateBiasAgent] Chunk failed: {e}")

        # 정렬: 문장 인덱스 순
        all_issues.sort(key=lambda x: x.get("sentence_index", -1))
            
        return {
            "issues": all_issues,
            "note": f"Analyzed {len(sentences)} sentences in {len(chunks)} chunks (Parallel)"
        }

    def _analyze_chunk(self, chunk: list[str], start_index: int, reader_context: dict | None = None) -> dict:
        system = """
You are a strict JSON generator. You MUST output valid JSON only.
"""
        import json
        split_context = json.dumps(chunk, ensure_ascii=False)
        
        persona_text = ""
        if reader_context:
            persona_text = f"\n[독자 특이사항]\n{json.dumps(reader_context, ensure_ascii=False)}\n위 독자의 배경지식이나 성향에 따라 '혐오/편견'으로 느껴질 수 있는 요소를 더욱 민감하게 탐지하라."

        prompt = f"""
너는 **이 독자의 가치관을 대변하는 '편견 감시자(Watchdog)'**이다.
입력은 원고의 문장 배열(JSON)이며, 시작 인덱스는 {start_index}이다.
각 이슈의 sentence_index는 {start_index} + (청크 내 인덱스)로 계산해야 한다.

핵심 원칙:
- 반드시 '집단적 속성'과 연결된 경우만 issue로 판단할 것
- **[독자 특이사항]**을 최우선 기준으로 삼아라. 이 독자가 모욕적이라고 느낄 수 있는 표현이라면, 사회적으로 용인되는 수준이라도 지적해야 한다.
{persona_text}

탐지 대상: 특정 집단 일반화, 성별/민족/직업 등 고정관념, 비하

출력 JSON 형식:
{{
  "issues": [
    {{
      "issue_type": "bias | hate | stereotype",
      "severity": "low | medium | high",
      "sentence_index": {start_index} + index,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "사유",
      "target": "집단/대상",
      "bias_type": "혐오 | 편견 | 비하 | 고정관념",
      "confidence": 0.0
    }}
  ]
}}

문장 배열:
{split_context}
"""
        response = chat(prompt, system=system)
        return self._safe_json_load(response)
