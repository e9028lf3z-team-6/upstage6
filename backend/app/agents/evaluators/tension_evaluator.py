from app.agents.evaluators.base_evaluator import BaseEvaluatorAgent

class TensionQualityAgent(BaseEvaluatorAgent):
    """
    Evaluates the performance of the TensionCurveAgent.
    """
    name = "tension-quality-judge"

    def run(self, original_text: str, agent_output: dict) -> dict:
        criteria = """
        **Specific Criteria for Tension Curve Analysis:**
        1. **Data Integrity**: Does the output provide a numerical curve or list of tension points?
        2. **Correlation**: Do the tension peaks correspond to actual dramatic moments in the text?
        3. **Low Tension**: Does it correctly identify boring or dragging sections?
        """
        return self.run_evaluation(original_text, agent_output, criteria)
