from fastapi import Depends, APIRouter

from app.deps import get_chat_service
from app.models.schemas.chat import ChatRequest
from app.service.chat_service import ChatService

chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("/tools")
async def chat_with_tools(
    message: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    result = await chat_service.chat_with_time_tool(message.prompt)
    return {"ai_message": result}
