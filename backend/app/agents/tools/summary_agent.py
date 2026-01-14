from app.agents.base import BaseAgent
from app.llm.chat import chat
import logging

logger = logging.getLogger(__name__)

class SummaryAgent(BaseAgent):
    """
    원고 전체의 핵심 맥락을 요약하는 에이전트
    """
    name = "summary-agent"

    def run(self, text: str) -> str:
        logger.info(f"[DEBUG] SummaryAgent: Summarizing text (len={len(text)})")
        
        system = "너는 소설 및 원고 분석을 돕는 전문 요약가이다. 제공된 텍스트의 핵심 줄거리, 등장인물 관계, 주요 설정, 복선을 작가와 분석관들이 참고하기 좋게 요약하라."
        
        prompt = f"""
        다음 원고를 읽고, 이후 분석 단계에서 '전체 맥락'으로 참고할 수 있도록 요약해줘.
        
        요약 지침:
        - 주요 사건 흐름 (줄거리)
        - 핵심 등장인물의 성격과 목표
        - 중요한 세계관 설정이나 복선
        - 현재 진행 중인 갈등 상황
        
        원고 내용:
        {text[:10000]}  # 너무 길면 앞부분 위주로 요약하되, 모델 한계까지 최대한 활용
        """
        
        response = chat(prompt, system=system)
        return response
