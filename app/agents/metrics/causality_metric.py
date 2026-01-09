# app/agents/metrics/causality_metric.py

from typing import Dict, List
from app.agents.base import BaseAgent


class CausalityMetricAgent(BaseAgent):
    """
    CausalityEvaluatorAgent 출력 품질 감시용 metrics Agent
    """

    name = "causality-metrics"

    def validate(
        self,
        issues: List[dict],
        reader_context: dict | None = None,
    ) -> Dict:

        knowledge_level = "중급"
        if reader_context:
            knowledge_level = reader_context.get("knowledge_level", "중급")

        issue_count = len(issues)

        expected_max = {
            "초급": 6,
            "중급": 5,
            "고급": 3,
        }.get(knowledge_level, 5)

        too_many_issues = issue_count > expected_max
        zero_issue_risk = issue_count == 0 and knowledge_level == "초급"

        type_counter = {}
        for issue in issues:
            t = issue.get("type", "unknown")
            type_counter[t] = type_counter.get(t, 0) + 1

        dominant_type = None
        if type_counter:
            dominant_type = max(type_counter, key=type_counter.get)

        skewed_distribution = (
            dominant_type is not None
            and type_counter[dominant_type] >= issue_count * 0.7
        )

        locations = [i.get("location") for i in issues if i.get("location")]
        duplicate_locations = len(locations) != len(set(locations))

        return {
            "metrics": "causality",
            "issue_count": issue_count,
            "knowledge_level": knowledge_level,
            "too_many_issues": too_many_issues,
            "zero_issue_risk": zero_issue_risk,
            "skewed_distribution": skewed_distribution,
            "duplicate_locations": duplicate_locations,
            "issue_type_distribution": type_counter,
            "note": "causality metrics evaluation completed",
        }

    # 하위 호환 (dev 단계에서는 매우 유용)
    def run(
        self,
        issues: List[dict],
        reader_context: dict | None = None,
    ) -> Dict:
        return self.validate(issues, reader_context)
