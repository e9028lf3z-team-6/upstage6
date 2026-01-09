from pydantic import BaseModel

class KnowledgeResponse(BaseModel):
    status: str
    message: str
    inserted: int = 0
