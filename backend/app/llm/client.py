import os
from openai import OpenAI
from app.core.settings import get_settings

_PLACEHOLDER_KEYS = {
    "your_upstage_api_key_here",
    "your_upstage_api_key",
    "your_api_key",
    "your_key",
    "change_me",
}


def resolve_upstage_api_key() -> str | None:
    key = os.getenv("UPSTAGE_API_KEY")
    if not key:
        key = get_settings().upstage_api_key
    if not key:
        return None
    stripped = key.strip()
    if not stripped:
        return None
    if stripped.lower() in _PLACEHOLDER_KEYS:
        return None
    return stripped


def has_upstage_api_key() -> bool:
    return resolve_upstage_api_key() is not None

def get_upstage_client() -> OpenAI:
    api_key = resolve_upstage_api_key()
    if not api_key:
        raise RuntimeError("UPSTAGE_API_KEY is not set")

    settings = get_settings()
    return OpenAI(
        api_key=api_key,
        base_url=settings.upstage_base_url or "https://api.upstage.ai/v1",
    )
