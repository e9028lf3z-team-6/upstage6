# app/agents/metrics/genre_cliche_metric.py

from typing import Dict, List
from app.agents.base import BaseAgent


class GenreClicheMetricAgent(BaseAgent):
    """
    GenreClicheAgent 출력 품질 감시용 metrics Agent

    원칙:
    - soft signal 검증 전용
    - pivot / rewrite 결정 금지
    - Aggregator에 영향 없음
    - 과잉 탐지 / 프롬프트 붕괴 감지 목적
    """

    name = "genre-cliche-metrics"

    def run(self, issues: List[dict]) -> Dict:

        issue_count = len(issues)

        # -----------------------------
        # 1. 개수 상한 체크
        # -----------------------------
        too_many_cliches = issue_count >= 4

        # -----------------------------
        # 2. 장르 중복 체크
        # -----------------------------
        genres = [i.get("genre") for i in issues if i.get("genre")]
        unique_genres = set(genres)

        repeated_genre = len(genres) != len(unique_genres)
        too_many_genres = len(unique_genres) >= 4

        # -----------------------------
        # 3. 패턴 설명 품질 체크
        # -----------------------------
        vague_patterns = 0
        for i in issues:
            pattern = i.get("pattern", "")
            if len(pattern.strip()) < 10:
                vague_patterns += 1

        low_quality_signal = vague_patterns >= max(1, issue_count // 2)

        # -----------------------------
        # 4. metrics 결과
        # -----------------------------
        return {
            "metrics": "genre_cliche",
            "issue_count": issue_count,
            "too_many_cliches": too_many_cliches,
            "repeated_genre": repeated_genre,
            "too_many_genres": too_many_genres,
            "low_quality_signal": low_quality_signal,
            "unique_genres": list(unique_genres),
            "note": "genre cliché metrics evaluation completed",
        }
