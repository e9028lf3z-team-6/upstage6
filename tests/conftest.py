import pytest

from tests.fakes.fake_time_service import FakeTimeService
from tests.fakes.fake_embedding_service import FakeEmbeddingService
from tests.fakes.fake_vector_repo import FakeVectorRepository

from app.service.vector_service import VectorService
from app.service.agent_service import AgentService

@pytest.fixture
def time_service():
    return FakeTimeService()

@pytest.fixture
def vector_service():
    repo = FakeVectorRepository()
    embed = FakeEmbeddingService()
    return VectorService(repo, embed)

@pytest.fixture
def agent_service(vector_service, time_service):
    return AgentService(
        vector_service=vector_service,
        time_service=time_service,
    )
