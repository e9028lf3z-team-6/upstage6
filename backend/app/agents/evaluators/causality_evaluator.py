from app.agents.evaluators.base_evaluator import BaseEvaluatorAgent

class CausalityQualityAgent(BaseEvaluatorAgent):
    """
    Evaluates the performance of the CausalityEvaluatorAgent.
    """
    name = "causality-quality-judge"

    def run(self, original_text: str, agent_output: dict) -> dict:
        criteria = """
        **Specific Criteria for Causality Analysis:**
        1. **Logic Focused**: Does the agent focus ONLY on logical gaps (Cause -> Effect)?
        2. **differentiation**: Does it distinguish between simple lack of detail vs. actual logical contradictions?
        3. **Negative Constraints**: Did the agent AVOID critiquing style/tone? (It should strictly check plot logic).
        4. **Specificity**: Are the 'from_event' and 'to_event' fields filled with identifiable parts of the text?
        """
        return self.run_evaluation(original_text, agent_output, criteria)
