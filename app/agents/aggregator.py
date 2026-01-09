from app.schemas.decision import AggregateResult, Decision

class AggregatorAgent:
    name = "aggregator"

    def run(self, tone_total: float) -> AggregateResult:
        # 임계값 설계 (지금은 단순)
        if tone_total >= 0.7:
            decision = Decision.PASS
            reason = "Tone is sufficiently clear and neutral."
        elif tone_total >= 0.4:
            decision = Decision.REWRITE
            reason = "Tone is understandable but too subjective."
        else:
            decision = Decision.REJECT
            reason = "Tone is overly subjective or impolite."

        return AggregateResult(
            tone_score=round(tone_total, 3),
            decision=decision,
            reason=reason,
        )
