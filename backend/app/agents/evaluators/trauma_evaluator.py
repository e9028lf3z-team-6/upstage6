from app.agents.evaluators.base_evaluator import BaseEvaluatorAgent

class TraumaQualityAgent(BaseEvaluatorAgent):
    """
    Evaluates the performance of the TraumaAgent.
    """
    name = "trauma-quality-judge"

    def run(self, original_text: str, agent_output: dict) -> dict:
        criteria = """
        **Specific Criteria for Trauma/Trigger Warning Analysis:**
        1. **Sensitivity**: Did it catch obvious triggers (violence, abuse, disaster)?
        2. **False Positives**: Did it avoid flagging metaphorical or mild expressions as severe trauma?
        3. **Categorization**: Are the identified issues categorized correctly (e.g., Physical vs Emotional)?
        """
        return self.run_evaluation(original_text, agent_output, criteria)
