import os
import json
from typing import Any, Dict

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

try:
    from langsmith import Client
    from langsmith.evaluation import evaluate
except Exception:  # pragma: no cover - optional dependency/runtime
    Client = None
    evaluate = None




def predictor(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the local eval API to get scores and outputs.
    """
    url = os.getenv("EVAL_API_URL", "http://127.0.0.1:8000/api/eval/run")
    payload = {
        "text": inputs.get("text"),
        "doc_id": inputs.get("doc_id"),
        "use_llm_judge": inputs.get("use_llm_judge", False),
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from exc


if __name__ == "__main__":
    sample_text = os.getenv("EVAL_TEXT")
    doc_id = os.getenv("EVAL_DOC_ID")
    use_llm_judge = os.getenv("USE_LLM_JUDGE", "false").lower() in ("1", "true", "yes", "on")

    if Client is None or evaluate is None:
        outputs = predictor({"text": sample_text, "doc_id": doc_id, "use_llm_judge": use_llm_judge})
        print(json.dumps(outputs, ensure_ascii=False, indent=2))
    else:
        dataset_name = os.getenv("EVAL_DATASET", "team-contextor-eval")
        client = Client()
        evaluate(
            dataset_name=dataset_name,
            predictor=lambda x: predictor({
                "text": x.get("text"),
                "doc_id": x.get("doc_id"),
                "use_llm_judge": use_llm_judge,
            }),
            evaluators=[],
            client=client,
        )
