import logging
import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.logging import init_logging
from app.exceptions import UserNotFoundError, EmailNotAllowedNameExistsError

from app.api.route.user_routers import router as user_router
from app.api.route.chat_router import chat_router
from app.api.route.agent_routers import router as agent_router

app = FastAPI()
init_logging()
logger = logging.getLogger(__name__)

load_dotenv()

# =========================
# Exception Handlers
# =========================

@app.exception_handler(EmailNotAllowedNameExistsError)
async def email_not_allowed_handler(request: Request, exc: EmailNotAllowedNameExistsError):
    logger.exception("Email Not Allowed exception occurred")
    return JSONResponse(
        status_code=409,
        content={"error": "Email Not Allowed", "message": str(exc)}
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    logger.exception("User Not Found exception occurred")
    return JSONResponse(
        status_code=404,
        content={"error": "User Not Found", "message": str(exc)}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.exception("Bad Request exception occurred")
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "message": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.exception("HTTP exception occurred")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Exception", "message": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "Something went wrong"}
    )

# =========================
# Routers
# =========================

logger.info("앱 시작")

app.include_router(user_router)
app.include_router(chat_router)
app.include_router(agent_router)    

# =========================
# Health Check
# =========================

@app.get("/hello")
async def hello():
    return {"message": "Hello FastAPI!"}
