import os
import uuid
import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from app.core.db import get_session, Document
from app.services.document_parser import document_parser
from app.webapi.schemas import DocumentDetail, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
async def list_documents():
    async with get_session() as session:
        res = await session.execute(select(Document).order_by(Document.created_at.desc()))
        items = res.scalars().all()
        return items


@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "Filename is required")

    doc_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    stored_name = f"{doc_id}{ext}"
    stored_path = Path("data/uploads") / stored_name
    stored_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    with stored_path.open("wb") as f:
        f.write(content)

    text, meta = await document_parser.extract_text(str(stored_path))
    title = Path(file.filename).stem or file.filename
    content_type = file.content_type or "application/octet-stream"

    doc = Document(
        id=doc_id,
        title=title,
        filename=file.filename,
        content_type=content_type,
        stored_path=str(stored_path),
        extracted_text=text,
        meta_json=json.dumps(meta, ensure_ascii=False),
    )

    async with get_session() as session:
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        return doc


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        stored_path = doc.stored_path
        await session.delete(doc)
        await session.commit()

    if stored_path and os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except OSError:
            pass

    return {"ok": True}
