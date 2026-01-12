from fastapi import APIRouter

# domain routers
from .documents import router as documents_router
from .analysis import router as analysis_router
from .eval import router as eval_router

# agent APIs
from app.api.router import router as tools_router
from app.api.develope_route import router as dev_metric_router


router = APIRouter()

# --------------------
# Core domain
# --------------------
router.include_router(documents_router)
router.include_router(analysis_router)
router.include_router(eval_router)

# --------------------
# Agent APIs
# --------------------
router.include_router(tools_router)       # /tools/*
router.include_router(dev_metric_router)  # /dev/*
