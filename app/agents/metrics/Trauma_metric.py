class TraumaMetric:
    def run(self, trauma_result: dict) -> dict:
        issues = trauma_result.get("issues", [])

        type_count = {}
        for issue in issues:
            t = issue.get("trigger_type")
            type_count[t] = type_count.get(t, 0) + 1

        return {
            "issue_count": len(issues),
            "trigger_type_distribution": type_count,
            "has_high_risk_type": any(
                t in ["생명위협", "재난"] for t in type_count
            )
        }
