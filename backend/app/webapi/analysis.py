import json, uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.db import get_session, Document, Analysis
from app.services.analysis_runner import run_analysis_for_text
from app.webapi.schemas import AnalysisOut, AnalysisDetail

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/run/{doc_id}", response_model=AnalysisOut)
async def run_analysis(doc_id: str, use_langgraph: bool = False):
    async with get_session() as session:
        d = await session.get(Document, doc_id)
        if not d:
            raise HTTPException(404, "Document not found")

        result = await run_analysis_for_text(d.extracted_text, use_langgraph=use_langgraph)

        a = Analysis(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            status="done",
            result_json=json.dumps(result, ensure_ascii=False),
        )
        session.add(a)
        await session.commit()
        return AnalysisOut(id=a.id, document_id=doc_id, status=a.status, created_at=str(a.created_at))

@router.get("/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(analysis_id: str):
    async with get_session() as session:
        a = await session.get(Analysis, analysis_id)
        if not a:
            raise HTTPException(404, "Analysis not found")
        return AnalysisDetail(
            id=a.id, document_id=a.document_id, status=a.status, created_at=str(a.created_at),
            result=json.loads(a.result_json)
        )

@router.get("/by-document/{doc_id}", response_model=list[AnalysisOut])
async def list_analyses_for_doc(doc_id: str):
    async with get_session() as session:
        res = await session.execute(select(Analysis).where(Analysis.document_id==doc_id).order_by(Analysis.created_at.desc()))
        items = res.scalars().all()
        return [AnalysisOut(id=i.id, document_id=i.document_id, status=i.status, created_at=str(i.created_at)) for i in items]


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str):
    async with get_session() as session:
        a = await session.get(Analysis, analysis_id)
        if not a:
            raise HTTPException(404, "Analysis not found")
        await session.delete(a)
        await session.commit()
    return {"ok": True}
