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
                    print(f"[HateBiasAgent] Chunk failed: {e}")

        # 정렬: 문장 인덱스 순
        all_issues.sort(key=lambda x: x.get("sentence_index", -1))
        
        # 전체 점수 계산 (평균) - 편향이 없을수록 높음
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
        split_context = json.dumps(chunk, ensure_ascii=False)

        prompt = f"""
너는 '혐오 및 편견 표현 탐지기'이다.
입력은 원고의 문장 배열(JSON)이며, 시작 인덱스는 {start_index}이다.
각 이슈의 sentence_index는 {start_index} + (청크 내 인덱스)로 계산해야 한다.

핵심 원칙:
- 반드시 '집단적 속성'과 연결된 경우만 issue로 판단할 것
- 모든 설명(reason, target, bias_type)은 반드시 한국어로 작성하라.
- 탐지 대상: 특정 집단 일반화, 성별/민족/직업 등 고정관념, 비하

출력 JSON 형식:
{{
  "score": <int 0-100, 혐오/편견 없는 청정 윤리 점수>,
  "issues": [
    {{
      "issue_type": "bias | hate | stereotype",
      "severity": "low | medium | high",
      "sentence_index": {start_index} + index,
      "char_start": 0,
      "char_end": 0,
      "quote": "문제 구간 원문 인용",
      "reason": "사유 (한국어로 작성)",
      "target": "집단/대상 (한국어로 작성)",
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
