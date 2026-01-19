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
    extracted_text: str
    title: str | None = None


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    current_user: User | None = Depends(get_current_user)
):
    async with get_session() as session:
        query = select(Document).order_by(Document.created_at.desc())
        
        if current_user:
            # 로그인 유저: 내 문서만 조회
            query = query.where(Document.user_id == current_user.id)
        else:
            # 비로그인 유저: 익명(user_id=None) 문서만 조회 (또는 빈 목록)
            query = query.where(Document.user_id == None)
            
        res = await session.execute(query)
        items = res.scalars().all()
        return items


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User | None = Depends(get_current_user)
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

    doc = Document(
        id=doc_id,
        user_id=current_user.id if current_user else None,
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
async def get_document(
    doc_id: str,
    current_user: User | None = Depends(get_current_user)
):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        
        # 권한 체크
        owner_id = doc.user_id
        request_user_id = current_user.id if current_user else None
        
        if owner_id != request_user_id:
             # 관리자 기능이 없다면 404 처리하여 존재 여부 숨김 (보안)
            raise HTTPException(404, "Document not found")
            
        return doc


@router.patch("/{doc_id}", response_model=DocumentDetail)
async def update_document(
    doc_id: str, 
    payload: DocumentUpdate,
    current_user: User | None = Depends(get_current_user)
):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        
        # 권한 체크
        owner_id = doc.user_id
        request_user_id = current_user.id if current_user else None
        
        if owner_id != request_user_id:
            raise HTTPException(404, "Document not found")
            
        doc.extracted_text = payload.extracted_text
        if payload.title is not None:
            doc.title = payload.title
        doc.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(doc)
        return doc


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User | None = Depends(get_current_user)
):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        
        # 권한 체크
        owner_id = doc.user_id
        request_user_id = current_user.id if current_user else None
        
        if owner_id != request_user_id:
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
