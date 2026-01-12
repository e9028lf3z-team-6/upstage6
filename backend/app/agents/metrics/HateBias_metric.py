# app/agents/metrics/hate_bias_metric.py

from typing import Dict, List
from backend.app.agents.base import BaseAgent


class HateBiasMetricAgent(BaseAgent):
    """
    HateBiasAgent 출력 검증용 metrics Agent

    목적:
    - 집단성 위반 오탐 방지
    - 과잉 hate 탐지 차단
    - Aggregator 신뢰도 보호

    원칙:
    - pivot 결정 금지
    - rewrite 판단 금지
    - Aggregator에 영향 없음
    """

    name = "hate-bias-metrics"

    GROUP_KEYWORDS = [
        "성별", "여성", "남성",
        "국가", "민족", "인종",
        "직업", "계층",
        "장애", "질병",
        "노인", "청소년", "아이들"
    ]

    def run(self, issues: List[dict]) -> Dict:

        issue_count = len(issues)

        # -----------------------------
        # 1. 집단성 검증
        # -----------------------------
        non_group_targets = 0
        personal_target_detected = False

        for issue in issues:
            target = issue.get("target", "")
            if not any(k in target for k in self.GROUP_KEYWORDS):
                non_group_targets += 1

            # 개인 이름 의심 신호
            if len(target) <= 4 and " " not in target:
                personal_target_detected = True

        # -----------------------------
        # 2. 품질 평가
        # -----------------------------
        low_quality = 0
        for issue in issues:
            desc = issue.get("description", "")
            if len(desc.strip()) < 20:
                low_quality += 1

        # -----------------------------
        # 3. 결과 요약
        # -----------------------------
        return {
            "metrics": "hate_bias",
            "issue_count": issue_count,
            "non_group_target_ratio": (
                non_group_targets / issue_count
                if issue_count else 0
            ),
            "personal_target_detected": personal_target_detected,
            "low_quality_signal": low_quality >= max(1, issue_count // 2),
            "note": "hate & bias metrics evaluation completed",
        }
