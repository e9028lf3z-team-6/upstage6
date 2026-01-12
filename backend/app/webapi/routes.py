from fastapi import APIRouter

from .documents import router as documents_router
from .analysis import router as analysis_router

from ..api.router import router as agent_router
from ..api.develope_route import router as dev_router

router = APIRouter()

router.include_router(documents_router)
router.include_router(analysis_router)

router.include_router(agent_router)
router.include_router(dev_router)
