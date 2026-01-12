from app.llm.client import get_upstage_client
from app.observability.langsmith import create_llm_run

CHAT_MODEL = "solar-pro2"

def chat(prompt: str, system: str | None = None) -> str:
    client = get_upstage_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    res = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.2,
    )
    usage = getattr(res, "usage", None)
    usage_payload = None
    if usage:
        usage_payload = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }
    create_llm_run(
        name="chat.completions",
        provider="upstage",
        model=CHAT_MODEL,
        inputs={"messages": messages},
        outputs={"content": res.choices[0].message.content},
        usage=usage_payload,
    )

    return res.choices[0].message.content
