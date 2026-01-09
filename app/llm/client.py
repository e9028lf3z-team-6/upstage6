import os
from openai import OpenAI

def get_upstage_client() -> OpenAI:
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("UPSTAGE_API_KEY is not set")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.upstage.ai/v1",
    )
