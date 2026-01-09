from fastapi import Depends

from app.repository.client.upstage_client import UpstageClient
from app.repository.vector_repo import ChromaDBRepository, VectorRepository

from app.service.time_service import TimeService
from app.service.embedding_service import EmbeddingService
from app.service.vector_service import VectorService
from app.service.agent_service import AgentService

from app.service.chat_service import ChatService

# =========================
# Singleton / Base Clients
# =========================

upstage_client = UpstageClient()


def get_upstage_client() -> UpstageClient:
    return upstage_client


# =========================
# Core Services
# =========================

def get_time_service() -> TimeService:
    return TimeService()


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


# =========================
# Vector / RAG
# =========================

def get_vector_repository() -> VectorRepository:
    # ChromaDB 연결
    return ChromaDBRepository()


def get_vector_service(
    vector_repository: VectorRepository = Depends(get_vector_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> VectorService:
    return VectorService(
        vector_repository=vector_repository,
        embedding_service=embedding_service,
    )


# =========================
# Agent
# =========================

def get_agent_service(
    vector_service: VectorService = Depends(get_vector_service),
    time_service: TimeService = Depends(get_time_service),
) -> AgentService:
    return AgentService(
        vector_service=vector_service,
        time_service=time_service,
    )


# =========================
# Legacy
# =========================

def get_chat_service(
    upstage_client: UpstageClient = Depends(get_upstage_client),
    time_service: TimeService = Depends(get_time_service),
) -> ChatService:
    return ChatService(
        upstage_client=upstage_client,
        time_service=time_service,
    )
