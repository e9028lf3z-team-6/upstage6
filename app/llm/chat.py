from app.llm.client import get_upstage_client

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

    return res.choices[0].message.content
