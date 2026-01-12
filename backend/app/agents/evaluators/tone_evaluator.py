from app.agents.evaluators.base_evaluator import BaseEvaluatorAgent

class ToneQualityAgent(BaseEvaluatorAgent):
    """
    Evaluates the performance of the ToneEvaluatorAgent.
    """
    name = "tone-quality-judge"

    def run(self, original_text: str, agent_output: dict) -> dict:
        criteria = """
        **Specific Criteria for Tone Analysis:**
        1. **Relevance**: Does the agent identify actual shifts in tone or awkward phrasing that hinders readability?
        2. **Objectivity**: Does it avoid subjective aesthetic judgments (e.g., "This is not beautiful")?
        3. **Context**: Does it correctly identify mixed formalities (e.g., mixing polite and casual speech)?
        4. **Negative Constraints**: Did the agent AVOID giving a score or rewriting the text? (It should only list issues).
        """
        return self.run_evaluation(original_text, agent_output, criteria)
