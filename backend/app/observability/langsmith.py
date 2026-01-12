import os
import time

try:
    from langsmith import Client as _LangSmithClient
    from langsmith import traceable as _traceable
    try:
        from langsmith.run_helpers import get_current_run_tree as _get_current_run_tree
    except Exception:
        _get_current_run_tree = None
except Exception:  # pragma: no cover - optional dependency/runtime
    _LangSmithClient = None
    _traceable = None
    _get_current_run_tree = None


def _is_enabled() -> bool:
    flags = [
        os.getenv("LANGSMITH_TRACING", ""),
        os.getenv("LANGCHAIN_TRACING_V2", ""),
    ]
    return any(v.lower() in ("1", "true", "yes", "on") for v in flags)


def traceable(*args, **kwargs):
    """
    LangSmith trace decorator with safe no-op fallback.
    Enabled when LANGSMITH_TRACING or LANGCHAIN_TRACING_V2 is truthy.
    """
    if _traceable is None or not _is_enabled():
        def decorator(func):
            return func
        return decorator
    return _traceable(*args, **kwargs)


def _get_run_id() -> str | None:
    if _get_current_run_tree is None:
        return None
    run_tree = _get_current_run_tree()
    if not run_tree:
        return None
    return getattr(run_tree, "id", None) or getattr(run_tree, "run_id", None)


def create_feedback(entries: list[dict]) -> bool:
    """
    Create LangSmith feedback entries for the current traced run.
    Each entry supports: key, score, value, comment.
    """
    if _LangSmithClient is None or not _is_enabled():
        return False
    run_id = _get_run_id()
    if not run_id:
        return False
    client = _LangSmithClient()
    for entry in entries:
        key = entry.get("key")
        if not key:
            continue
        try:
            client.create_feedback(
                run_id=run_id,
                key=key,
                score=entry.get("score"),
                value=entry.get("value"),
                comment=entry.get("comment"),
            )
        except Exception:
            continue
    return True


def traceable_timed(name: str):
    """
    Traceable decorator for tool runs (uses LangSmith standard run_type="tool").
    """
    def decorator(func):
        @traceable(name=name, run_type="tool")
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def create_llm_run(
    name: str,
    provider: str,
    model: str,
    inputs: dict,
    outputs: dict,
    usage: dict | None,
) -> bool:
    """
    Create a child LLM run with standard usage fields for LangSmith dashboards.
    """
    if _LangSmithClient is None or not _is_enabled():
        return False
    parent_run_id = _get_run_id()
    if not parent_run_id:
        return False
    client = _LangSmithClient()
    extra = {"usage": usage} if usage else None
    metadata = {"ls_provider": provider, "ls_model_name": model}
    try:
        client.create_run(
            name=name,
            run_type="llm",
            parent_run_id=parent_run_id,
            inputs=inputs,
            outputs=outputs,
            extra=extra,
            metadata=metadata,
        )
    except Exception:
        return False
    return True
