from pydantic import BaseModel

class AgentRequest(BaseModel):
    text: str
    expected: dict | None = None

class AgentResponse(BaseModel):
    agent: str
    result: dict | str
