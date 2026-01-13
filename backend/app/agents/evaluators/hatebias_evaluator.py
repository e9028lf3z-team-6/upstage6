from app.agents.evaluators.base_evaluator import BaseEvaluatorAgent

class HateBiasQualityAgent(BaseEvaluatorAgent):
    """
    Evaluates the performance of the HateBiasAgent.
    """
    name = "hatebias-quality-judge"

    def run(self, original_text: str, agent_output: dict) -> dict:
        criteria = """
        **Specific Criteria for Hate/Bias Analysis:**
        1. **Detection**: Did it find discriminatory language against protected groups (race, gender, disability, etc.)?
        2. **Context Awareness**: Does it distinguish between a character being hateful (portrayal) vs. the narrative being hateful (endorsement)?
        3. **Severity**: Is the severity assessment reasonable?
        """
        return self.run_evaluation(original_text, agent_output, criteria)
