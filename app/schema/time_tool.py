from enum import Enum
from pydantic import BaseModel, Field


class TimeZoneEnum(str, Enum):
    Asia_Seoul = "Asia/Seoul"
    America_New_York = "America/New_York"
    Europe_London = "Europe/London"


class GetCurrentTimeArgs(BaseModel):
    timezone: TimeZoneEnum = Field(...)


GET_CURRENT_TIME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Retrieves current time for the given timezone.",
        "parameters": GetCurrentTimeArgs.model_json_schema(),
    },
}
