from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, List

from app.deps import get_agent_service
from app.service.agent_service import AgentService

router = APIRouter(prefix="", tags=["agent"])


# =========================
# Schemas
# =========================

class KnowledgeRequest(BaseModel):
    documents: List[str]
    metadatas: List[Dict[str, Any]] | None = None


class KnowledgeResponse(BaseModel):
    status: str
    message: str
    inserted: int


class QueryRequest(BaseModel):
    question: str = Field(..., description="사용자 질문")
    context_limit: int = Field(3, ge=1, le=10)


class QueryResponse(BaseModel):
    question: str
    ai_message: str


# =========================
# APIs
# =========================

@router.post("/knowledge", response_model=KnowledgeResponse)
async def add_knowledge(
    req: KnowledgeRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    result = agent_service.add_knowledge(
        documents=req.documents,
        metadatas=req.metadatas,
    )
    return KnowledgeResponse(**result)


@router.post("/query", response_model=QueryResponse)
async def query_agent(
    req: QueryRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    result = agent_service.process_query(
        query=req.question,
        context_limit=req.context_limit,
    )
    return QueryResponse(**result)
