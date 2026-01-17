import os
import uuid
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy import select
from pydantic import BaseModel

from app.core.db import get_session, Document, User
from app.core.auth import get_current_user
from app.services.document_parser import document_parser
from app.webapi.schemas import DocumentDetail, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentUpdate(BaseModel):
    extracted_text: str | None = None
    title: str | None = None
    settings: dict | None = None


@router.get("", response_model=list[DocumentOut])
async def list_documents(user: User | None = Depends(get_current_user)):
    if not user:
        return []
        
    async with get_session() as session:
        # Filter by current user
        res = await session.execute(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.created_at.desc())
        )
        items = res.scalars().all()
        return items


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    user: User | None = Depends(get_current_user)
):
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
    
    user_id = user.id if user else None

    doc = Document(
        id=doc_id,
        user_id=user_id,
        title=title,
        filename=file.filename,
        content_type=content_type,
        stored_path=str(stored_path),
        extracted_text=text,
        meta_json=json.dumps(meta, ensure_ascii=False),
        updated_at=datetime.utcnow(),
    )

    async with get_session() as session:
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str, user: User | None = Depends(get_current_user)):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
            
        # Permission check: Allow if doc is anonymous (user_id is None) OR owned by current user
        if doc.user_id is not None:
            if not user or doc.user_id != user.id:
                raise HTTPException(403, "Not authorized to access this document")
                
        return doc


@router.patch("/{doc_id}", response_model=DocumentDetail)
async def update_document(
    doc_id: str, 
    payload: DocumentUpdate,
    user: User | None = Depends(get_current_user)
):
    print(f"Updating document {doc_id} with payload: {payload}")
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
            
        if doc.user_id is not None:
            if not user or doc.user_id != user.id:
                raise HTTPException(403, "Not authorized to update this document")
        
        if payload.extracted_text is not None:
            doc.extracted_text = payload.extracted_text
        
        if payload.title is not None:
            doc.title = payload.title
            
        if payload.settings is not None:
            try:
                meta = json.loads(doc.meta_json or "{}")
            except json.JSONDecodeError:
                meta = {}
            
            # settings merge
            meta["settings"] = {**(meta.get("settings") or {}), **payload.settings}
            print(f"Updated meta settings: {meta['settings']}")
            doc.meta_json = json.dumps(meta, ensure_ascii=False)

        doc.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(doc)
        print(f"Document updated. Meta JSON: {doc.meta_json}")
        return doc


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, user: User | None = Depends(get_current_user)):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
            
        if doc.user_id is not None:
            if not user or doc.user_id != user.id:
                raise HTTPException(403, "Not authorized to delete this document")
            
        stored_path = doc.stored_path
        await session.delete(doc)
        await session.commit()

    if stored_path and os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except OSError:
            pass

    return {"ok": True}
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        if doc.user_id != user.id:
            raise HTTPException(403, "Not authorized to delete this document")
            
        stored_path = doc.stored_path
        await session.delete(doc)
        await session.commit()

    if stored_path and os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except OSError:
            pass

    return {"ok": True}
