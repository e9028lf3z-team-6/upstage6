from pydantic import BaseModel
from enum import Enum

class Decision(str, Enum):
    PASS = "pass"
    REWRITE = "rewrite"
    REJECT = "reject"


class AggregateResult(BaseModel):
    tone_score: float
    decision: Decision
    reason: str
