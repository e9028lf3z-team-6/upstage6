import json
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI


def get_current_time(timezone: str):
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        return json.dumps({"error": "invalid timezone"})

    now = datetime.now(tz)
    return json.dumps(
        {
            "timezone": timezone,
            "datetime": now.isoformat(),
            "hhmm": now.strftime("%H:%M"),
        }
    )


def run_conversation(client: OpenAI):
    messages = [
        {
            "role": "user",
            "content": "get_current_time 함수를 사용해서 Asia/Seoul과 America/New_York의 현재 시간을 알려줘",
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Retrieves current time for the given timezone.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "enum": [
                                "Asia/Seoul",
                                "America/New_York",
                                "Europe/London",
                            ],
                        }
                    },
                    "required": ["timezone"],
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model="solar-pro2",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "get_current_time": get_current_time,
        }

        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            function_response = available_functions[function_name](
                timezone=function_args["timezone"]
            )

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )

        second_response = client.chat.completions.create(
            model="solar-pro2",
            messages=messages,
        )
        return second_response

    return response_message
