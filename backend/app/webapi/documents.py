import os, uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import select

from app.core.db import get_session, Document
from app.services.document_parser import document_parser
from app.webapi.schemas import DocumentOut, DocumentDetail

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("", response_model=list[DocumentOut])
async def list_documents():
    async with get_session() as session:
        res = await session.execute(select(Document).order_by(Document.created_at.desc()))
        docs = res.scalars().all()
        return [DocumentOut(
            id=d.id, title=d.title, filename=d.filename, content_type=d.content_type, created_at=str(d.created_at)
        ) for d in docs]

@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".pdf",".docx",".txt",".md"}:
        raise HTTPException(400, f"Unsupported file type: {ext}. Use PDF/DOCX/TXT/MD.")

    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}{ext}"
    stored_path = Path("./data/uploads") / safe_name
    content = await file.read()
    stored_path.write_bytes(content)

    try:
        text, meta = await document_parser.extract_text(str(stored_path), file.content_type)
    except Exception as e:
        raise HTTPException(400, f"Failed to parse document: {e}")

    title = Path(file.filename).stem

    async with get_session() as session:
        d = Document(
            id=doc_id,
            title=title,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            stored_path=str(stored_path),
            extracted_text=text,
        )
        session.add(d)
        await session.commit()

    return DocumentOut(id=doc_id, title=title, filename=file.filename, content_type=d.content_type, created_at=str(d.created_at))

@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str):
    async with get_session() as session:
        d = await session.get(Document, doc_id)
        if not d:
            raise HTTPException(404, "Document not found")
        return DocumentDetail(
            id=d.id, title=d.title, filename=d.filename, content_type=d.content_type, created_at=str(d.created_at),
            extracted_text=d.extracted_text
        )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and all related analyses (cascade).

    Also removes the uploaded file from ./data/uploads if it exists.
    """
    async with get_session() as session:
        d = await session.get(Document, doc_id)
        if not d:
            raise HTTPException(404, "Document not found")

        # best-effort file cleanup
        try:
            if d.stored_path and os.path.exists(d.stored_path):
                os.remove(d.stored_path)
        except Exception:
            # don't block DB delete on filesystem issues
            pass

        await session.delete(d)
        await session.commit()

    return {"ok": True}
