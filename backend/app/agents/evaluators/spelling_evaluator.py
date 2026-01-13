from app.agents.evaluators.base_evaluator import BaseEvaluatorAgent


class SpellingQualityAgent(BaseEvaluatorAgent):
    """
    Evaluates the performance of the SpellingAgent.
    """
    name = "spelling-quality-judge"

    def run(self, original_text: str, agent_output: dict) -> dict:
        criteria = """
        **Specific Criteria for Spelling/Spacing Analysis:**
        1. **Scope**: Does it only flag spelling, spacing, particle, or nonstandard usage errors?
        2. **No Content Critique**: Did it avoid tone/style/logic judgments?
        3. **Localization**: Are sentence_index and char ranges provided when possible?
        4. **Clarity**: Are 'original' and 'description' concrete and actionable?
        """
        return self.run_evaluation(original_text, agent_output, criteria)
