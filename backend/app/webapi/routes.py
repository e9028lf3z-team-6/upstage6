from fastapi import APIRouter
from .documents import router as documents_router
from .analysis import router as analysis_router
from .auth import router as auth_router

router = APIRouter()
router.include_router(documents_router)
router.include_router(analysis_router)
router.include_router(auth_router, prefix="/auth", tags=["auth"])
