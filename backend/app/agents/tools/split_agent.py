from app.agents.base import BaseAgent
from app.llm.chat import chat
from app.llm.embedding import embed_text

"""
[SplitAgent]

역할:
- 입력 원고를 평가 가능한 구조로 "분리"하는 전처리 에이전트
- 이 단계에서는 절대 평가, 점수 산출, 수정 제안을 하지 않는다

설계 의도:
- 단일 원문을 그대로 평가하면 에이전트별 해석 편차(편향)가 발생할 수 있음
- SplitAgent는 모든 평가 에이전트가 공유하는 공통 해석 컨텍스트를 제공함
- Tone / Logic / Safety 에이전트는 이 split 결과를 기준으로만 판단을 수행함

책임 범위:
- 수행 o : 구조적 분석, 사실 관찰, 요소 분리
- 수행 x : 판단, 점수, 강점/약점 평가, 수정 방향 제시

분리 항목:
1. 말투: 문체, 대화체/서술체 여부, 감정 표현 방식 등 (관찰적 설명)
2. 인과관계: 사건의 흐름과 원인-결과 관계 요약
3. 장르: 텍스트의 성격 및 장르적 특징에 대한 추정
4. 잠재적 문제 표현: 이후 Safety 평가에 참고할 수 있는 표현 목록

출력:
- split_text: LLM이 생성한 구조적 분석 결과 (내부 평가용 컨텍스트)
- embedding_dim: 원문 기준 임베딩 차원 정보 (검색/확장 대비 메타데이터)

주의:
- split_text는 사용자에게 직접 노출되는 최종 결과가 아님
- 이후 모든 평가/판단 단계의 기반 데이터로 사용됨
"""



class SplitAgent(BaseAgent):
    name = "split-tools"

    def run(self, input_data: str) -> dict:
        split_prompt = f"""
        다음 원고를 '평가하지 말고', 구조적으로만 분석하라.

        목표:
        - 평가, 점수, 개선 제안은 하지 말 것
        - 사실 관찰과 구조 요약만 수행

        분리 항목:
        1. 말투 (관찰적 서술)
        2. 인과관계 (사건 흐름 요약)
        3. 장르 (추정)
        4. 잠재적으로 문제될 수 있는 표현 (목록화)

        원고:
        {input_data}
        """

        split_text = chat(split_prompt)
        embedding = embed_text(input_data)

        return {
            "split_text": split_text,
            "embedding_dim": len(embedding),
        }
