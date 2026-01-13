from app.agents.evaluators.base_evaluator import BaseEvaluatorAgent

class GenreClicheQualityAgent(BaseEvaluatorAgent):
    """
    Evaluates the performance of the GenreClicheAgent.
    """
    name = "cliche-quality-judge"

    def run(self, original_text: str, agent_output: dict) -> dict:
        criteria = """
        **Specific Criteria for Genre/Cliche Analysis:**
        1. **Genre Recognition**: Did it identify typical tropes relevant to the text's genre?
        2. **Originality**: Does it correctly assess whether a cliche is used creatively or lazily?
        3. **Over-detection**: Did it avoid flagging standard necessary plot devices as negative cliches?
        """
        return self.run_evaluation(original_text, agent_output, criteria)
