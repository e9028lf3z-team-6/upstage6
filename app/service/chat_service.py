from typing import AsyncGenerator

from app.models.schemas.chat import ChatRequest
from app.repository.client.upstage_client import UpstageClient
from app.service.time_service import TimeService
from app.schema.time_tool import GET_CURRENT_TIME_TOOL
import json
from datetime import datetime


class ChatService:
    def __init__(
        self,
        upstage_client: UpstageClient,
        time_service: TimeService,
    ):
        self.client = upstage_client
        self.time_service = time_service

    async def chat(self, message: ChatRequest) -> AsyncGenerator[str, None]:
        async for chunk in self.client.chat_streaming(message):
            yield chunk

    async def upstage_chat(self, message: ChatRequest):
        async for chunk in self.client.chat_streaming(message):
            yield chunk

    import json

    async def chat_with_time_tool(self, prompt: str) -> str:
        if any(k in prompt for k in ["날씨", "기온", "weather", "temperature"]):
            return "이 엔드포인트는 시간 조회만 지원합니다. 예: Asia/Seoul 현재 시간"

        response = self.client.chat_with_tools(prompt, tools=[GET_CURRENT_TIME_TOOL])

        if hasattr(response, "model_dump"):
            raw = response.model_dump()
        else:
            raw = response

        message = raw["choices"][0]["message"]
        tool_calls = message.get("tool_calls")

        times = {}

        if tool_calls:
            for call in tool_calls:
                fn = call.get("function", {})
                if fn.get("name") != "get_current_time":
                    continue
                args = json.loads(fn.get("arguments", "{}"))
                tz = args.get("timezone")
                if not tz:
                    continue
                t = self.time_service.get_current_time(tz)
                times[tz] = t
        else:
            for tz in ["Asia/Seoul", "America/New_York", "Europe/London"]:
                if tz in prompt:
                    t = self.time_service.get_current_time(tz)
                    times[tz] = t

        if not times:
            return message.get("content", "")

        order = [tz for tz in ["Asia/Seoul", "America/New_York", "Europe/London"] if tz in times]
        parts = [f"{tz}: {times[tz].hhmm}" for tz in order]

        if len(order) >= 2:
            dt_a = datetime.fromisoformat(times[order[0]].datetime_iso)
            dt_b = datetime.fromisoformat(times[order[1]].datetime_iso)
            off_a = dt_a.utcoffset()
            off_b = dt_b.utcoffset()
            if off_a is not None and off_b is not None:
                diff_min = int((off_a - off_b).total_seconds() // 60)
                diff_hr = abs(diff_min) // 60
                return " / ".join(parts) + f" (시차: {diff_hr}시간)"

        return " / ".join(parts)