import json
import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from rq import Queue
from redis import Redis

from app.core.db import get_session, Document, Analysis
from app.services.analysis_runner import run_analysis_for_text
from app.services.analysis_jobs import run_analysis_job, _collect_issue_counts, _is_fallback
from app.core.settings import get_settings
from app.webapi.schemas import AnalysisOut, AnalysisDetail

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/run/{doc_id}", response_model=AnalysisOut)
async def run_analysis(doc_id: str):
    async with get_session() as session:
        d = await session.get(Document, doc_id)
        if not d:
            raise HTTPException(404, "Document not found")

        result = await run_analysis_for_text(d.extracted_text, context=d.meta_json)
        status = "fallback" if _is_fallback(result) else "done"
        issue_counts = _collect_issue_counts(result)
        has_issues = any(v > 0 for v in issue_counts.values())

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


@router.post("/queue/run/{doc_id}", response_model=AnalysisOut)
async def queue_analysis(doc_id: str):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")

        analysis = Analysis(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            status="queued",
            result_json=json.dumps({"note": "queued"}, ensure_ascii=False),
        )
        session.add(analysis)
        await session.commit()

    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    queue = Queue("analysis", connection=redis)
    job = queue.enqueue(run_analysis_job, analysis.id, doc_id)

    async with get_session() as session:
        analysis_row = await session.get(Analysis, analysis.id)
        if analysis_row:
            analysis_row.queue_job_id = job.id
            await session.commit()

    return AnalysisOut(
        id=analysis.id,
        document_id=doc_id,
        status=analysis.status,
        created_at=str(analysis.created_at),
    )


@router.get("/queue/status/{analysis_id}")
async def queue_status(analysis_id: str):
    async with get_session() as session:
        analysis = await session.get(Analysis, analysis_id)
        if not analysis:
            raise HTTPException(404, "Analysis not found")

    job_id = analysis.queue_job_id
    if not job_id:
        return {"status": analysis.status, "progress": None, "job_id": None}

    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    queue = Queue("analysis", connection=redis)
    job = queue.fetch_job(job_id)
    if not job:
        return {"status": analysis.status, "progress": None, "job_id": job_id}

    progress = job.meta.get("progress")
    return {"status": job.get_status(), "progress": progress, "job_id": job.id}
