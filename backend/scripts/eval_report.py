import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def fetch_eval() -> str:
    url = os.getenv("EVAL_API_URL", "http://127.0.0.1:8000/api/eval/run")
    payload = {
        "text": os.getenv("EVAL_TEXT"),
        "doc_id": os.getenv("EVAL_DOC_ID"),
        "use_llm_judge": os.getenv("USE_LLM_JUDGE", "false").lower() in ("1", "true", "yes", "on"),
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=60) as resp:
            return resp.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from exc


if __name__ == "__main__":
    print(fetch_eval())
