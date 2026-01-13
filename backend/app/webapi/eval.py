from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from app.services.eval_runner import evaluate_text
from app.services.eval_report import render_eval_report

router = APIRouter(prefix="/eval", tags=["eval"])


class EvalRequest(BaseModel):
    text: str | None = None
    doc_id: str | None = None
    use_llm_judge: bool = False
    response_format: str = "text"


@router.post("/run", response_class=PlainTextResponse)
async def run_eval(req: EvalRequest):
    try:
        payload = await evaluate_text(
            text=req.text,
            doc_id=req.doc_id,
            use_llm_judge=req.use_llm_judge,
        )
        if req.response_format.lower() == "json":
            return JSONResponse(payload)
        return render_eval_report(payload)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
