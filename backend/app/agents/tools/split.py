from app.agents.base import BaseAgent
from app.services.split_map import build_split_payload
import logging

logger = logging.getLogger(__name__)

"""
[Splitter]

역할:
- 입력 원고를 평가 가능한 구조로 "분리"하는 전처리 도구
- 이 단계에서는 절대 평가, 점수 산출, 수정 제안을 하지 않는다

설계 의도:
- 단일 원문을 그대로 평가하면 에이전트별 해석 편차(편향)가 발생할 수 있음
- Splitter는 모든 평가 에이전트가 공유하는 공통 해석 컨텍스트를 제공함
- Tone / Logic / Safety 에이전트는 이 split 결과를 기준으로만 판단을 수행함

책임 범위:
- 수행 o : 구조적 분석, 사실 관찰, 요소 분리
- 수행 x : 판단, 점수, 강점/약점 평가, 수정 방향 제시

분리 항목:
1. 문장 단위 분리
2. 문장 매핑 정보 생성

출력:
- split_sentences: 문장 단위 분리 결과
- split_map: 문장별 오프셋/매핑 정보
- embedding_dim: 원문 기준 임베딩 차원 정보 (검색/확장 대비 메타데이터)

주의:
- split 결과는 사용자에게 직접 노출되는 최종 결과가 아님
- 이후 모든 평가/판단 단계의 기반 데이터로 사용됨
"""


class Splitter(BaseAgent):
    name = "split"

    def run(self, input_data: str) -> dict:
        logger.info(f"[DEBUG] Splitter.run: Input len={len(input_data)}")
        
        # REMOVED: embed_text call causing 400 Bad Request on large texts
        # embedding = embed_text(input_data)
        
        # Use a dummy dimension or None, as the actual vector wasn't being used anyway
        dummy_embedding_dim = 4096 

        logger.info("[DEBUG] Splitter.run: Calling build_split_payload...")
        result = build_split_payload(
            input_data,
            embedding_dim=dummy_embedding_dim,
        )
        logger.info("[DEBUG] Splitter.run: build_split_payload done.")
        return result
