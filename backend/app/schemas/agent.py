from pydantic import BaseModel

class AgentRequest(BaseModel):
    text: str

class AgentResponse(BaseModel):
    agent: str
    result: dict | str
