import json, uuid, logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.core.db import get_session, Document, Analysis, User
from app.core.auth import get_current_user
from app.services.analysis_runner import run_analysis_for_text, stream_analysis_for_text
from app.webapi.schemas import AnalysisOut, AnalysisDetail

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/run-stream/{doc_id}")
async def run_analysis_stream(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    mode = "full" if current_user else "causality_only"

    # 세션을 미리 열어 문서 정보를 가져온 뒤 닫음
    async with get_session() as session:
        d = await session.get(Document, doc_id)
        if not d:
            raise HTTPException(404, "Document not found")
        extracted_text = d.extracted_text
        meta_json = d.meta_json

    async def event_generator():
        try:
            async for event in stream_analysis_for_text(extracted_text, context=meta_json, mode=mode):
                if event["type"] == "final_result":
                    final_result = event["data"]
                    
                    issue_counts = _collect_issue_counts(final_result)
                    has_issues = any(v > 0 for v in issue_counts.values())
                    status = "fallback" if _is_fallback(final_result) else "done"
                    
                    # 최종 결과를 DB에 저장하기 위해 새로운 세션 생성
                    async with get_session() as internal_session:
                        a = Analysis(
                            id=str(uuid.uuid4()),
                            document_id=doc_id,
                            status=status,
                            decision=final_result.get("decision"),
                            has_issues=has_issues,
                            issue_counts_json=json.dumps(issue_counts, ensure_ascii=False),
                            result_json=json.dumps(jsonable_encoder(final_result), ensure_ascii=False),
                        )
                        internal_session.add(a)
                        await internal_session.commit()
                        event["analysis_id"] = a.id
                
                yield json.dumps(jsonable_encoder(event), ensure_ascii=False) + "\n"
        except Exception as e:
            logger.error(f"[API_STREAM] Generator error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(
        event_generator(), 
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Nginx 사용 시 버퍼링 방지
        }
    )

def _issue_count(result: dict | None) -> int:
    if not result:
        return 0
    issues = result.get("issues", [])
    return len(issues) if isinstance(issues, list) else 0


def _collect_issue_counts(result: dict) -> dict:
    return {
        "tone": _issue_count(result.get("tone")),
        "logic": _issue_count(result.get("logic")),
        "trauma": _issue_count(result.get("trauma")),
        "hate_bias": _issue_count(result.get("hate_bias")),
        "genre_cliche": _issue_count(result.get("genre_cliche")),
        "spelling": _issue_count(result.get("spelling")),
    }


def _is_fallback(result: dict) -> bool:
    report = result.get("final_report") or {}
    if isinstance(report, dict) and isinstance(report.get("note"), str):
        return "LLM 미사용" in report.get("note")
    return False

@router.post("/run/{doc_id}", response_model=AnalysisOut)
async def run_analysis(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    # Determine analysis mode based on login status
    mode = "full" if current_user else "causality_only"

    async with get_session() as session:
        d = await session.get(Document, doc_id)
        if not d:
            raise HTTPException(404, "Document not found")

        result = await run_analysis_for_text(
            d.extracted_text,
            context=d.meta_json,
            mode=mode,
        )
        issue_counts = _collect_issue_counts(result)
        has_issues = any(v > 0 for v in issue_counts.values())
        status = "fallback" if _is_fallback(result) else "done"

        a = Analysis(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            status=status,
            decision=result.get("decision"),
            has_issues=has_issues,
            issue_counts_json=json.dumps(issue_counts, ensure_ascii=False),
            result_json=json.dumps(result, ensure_ascii=False),
        )
        session.add(a)
        await session.commit()
        return AnalysisOut(
            id=a.id,
            document_id=doc_id,
            status=a.status,
            decision=a.decision,
            has_issues=a.has_issues,
            issue_counts=issue_counts,
            created_at=str(a.created_at),
        )

@router.get("/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(analysis_id: str):
    async with get_session() as session:
        a = await session.get(Analysis, analysis_id)
        if not a:
            raise HTTPException(404, "Analysis not found")
        return AnalysisDetail(
            id=a.id,
            document_id=a.document_id,
            status=a.status,
            decision=a.decision,
            has_issues=a.has_issues,
            issue_counts=json.loads(a.issue_counts_json or "{}"),
            created_at=str(a.created_at),
            result=json.loads(a.result_json),
        )

@router.get("/by-document/{doc_id}", response_model=list[AnalysisOut])
async def list_analyses_for_doc(doc_id: str):
    async with get_session() as session:
        res = await session.execute(select(Analysis).where(Analysis.document_id==doc_id).order_by(Analysis.created_at.desc()))
        items = res.scalars().all()
        out = []
        for i in items:
            issue_counts = json.loads(i.issue_counts_json or "{}")
            out.append(AnalysisOut(
                id=i.id,
                document_id=i.document_id,
                status=i.status,
                decision=i.decision,
                has_issues=i.has_issues,
                issue_counts=issue_counts,
                created_at=str(i.created_at),
            ))
        return out


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str):
    async with get_session() as session:
        a = await session.get(Analysis, analysis_id)
        if not a:
            raise HTTPException(404, "Analysis not found")
        await session.delete(a)
        await session.commit()
    return {"ok": True}
