from app.agents.base import BaseAgent
from app.llm.chat import chat
import json
import re

class BaseEvaluatorAgent(BaseAgent):
    """
    Base class for all Evaluator Agents (Judges).
    Evaluates the output of another agent against the original input text.
    """

    def run_evaluation(self, original_text: str, agent_output: dict, criteria: str) -> dict:
        """
        Evaluates the agent_output based on the original_text and specific criteria.
        
        Args:
            original_text: The input text that was analyzed.
            agent_output: The JSON output from the target agent.
            criteria: Specific evaluation criteria prompt.

        Returns:
            JSON dict with score (0-100), reasoning, and feedback.
        """
        system = """
        You are a strict QA (Quality Assurance) Auditor for an AI Analysis System.
        Your job is to evaluate the performance of a specific Analysis Agent.
        Output MUST be valid JSON only. No markdown.
        """

        prompt = f"""
        ### Task
        Evaluate the quality of the analysis provided by an AI Agent.
        
        ### Input Data
        1. **Original Text (Snippet/Summary)**:
        {original_text[:3000]} (Truncated if too long)

        2. **Agent's Analysis Output**:
        {json.dumps(agent_output, ensure_ascii=False, indent=2)}

        ### Evaluation Criteria
        {criteria}

        ### Scoring Rubric (0-100)
        - 90-100: Perfect detection, highly specific, follows all constraints.
        - 70-89: Good detection, minor misses or slightly vague.
        - 50-69: Acceptable but missed key issues or included hallucinations.
        - 30-49: Poor quality, vague, or violated negative constraints.
        - 0-29: Completely wrong or broken output.

        ### Output Format (JSON)
        {{
            "score": <int 0-100>,
            "reason": "<One sentence summary of the score>",
            "strengths": ["<point 1>", "<point 2>"],
            "weaknesses": ["<point 1>", "<point 2>"],
            "suggestion": "<How to improve prompts or logic>"
        }}
        """

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
