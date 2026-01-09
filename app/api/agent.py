from fastapi import APIRouter
from app.schemas.agent import AgentRequest
from app.agents.split_agent import SplitAgent
from app.agents.tone_evaluator import ToneEvaluatorAgent
from app.agents.aggregator import AggregatorAgent

router = APIRouter(prefix="/agent", tags=["agent"])

split_agent = SplitAgent()
tone_agent = ToneEvaluatorAgent()

aggregator = AggregatorAgent()

@router.post("/run")
def run_agent(req: AgentRequest):
    split_result = split_agent.run(req.text)
    tone_score = tone_agent.run(split_result["split_text"])
    aggregate = aggregator.run(tone_score.total)

    return {
        "agent": "pipeline",
        "split": split_result,
        "tone_score": tone_score.dict(),
        "tone_total": tone_score.total,
        "aggregate": aggregate.dict(),
    }